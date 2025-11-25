#!/usr/bin/env python3
"""CLI script to import SMS Backup & Restore XML files into Retext database."""

import argparse
import hashlib
import sys
import time
from xml.etree.ElementTree import iterparse

import db


def compute_import_hash(timestamp, phone_number, body):
    """Compute SHA256 hash for deduplication (T016)."""
    data = f"{timestamp}{phone_number}{body}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def count_messages(file_path):
    """Count total messages in XML file for progress tracking."""
    count = 0
    try:
        for event, elem in iterparse(file_path, events=['end']):
            if elem.tag == 'sms':
                count += 1
                elem.clear()
    except Exception:
        return None
    return count


def import_xml(file_path):
    """
    Import SMS messages from XML backup file.

    Returns tuple of (imported_count, duplicate_count, error_message).
    """
    # Initialize database
    db.init_db()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Get total count for progress (T018)
    print(f"Counting messages in {file_path}...")
    total = count_messages(file_path)
    if total is None:
        return 0, 0, "Failed to parse XML file"

    print(f"Found {total:,} messages")

    imported = 0
    duplicates = 0
    batch = []
    batch_size = 1000  # T017: 1000-record transactions

    try:
        # T014: Streaming XML parser using iterparse
        context = iterparse(file_path, events=['end'])

        for event, elem in context:
            if elem.tag != 'sms':
                continue

            # T015: Extract message fields
            phone_number = elem.get('address', '')
            body = elem.get('body', '')
            timestamp = elem.get('date', '0')
            message_type = elem.get('type', '1')
            contact_name = elem.get('contact_name')

            # Skip invalid messages
            if not phone_number or not body:
                elem.clear()  # T019: Clear element to bound memory
                continue

            # Convert types
            try:
                timestamp = int(timestamp)
                message_type = int(message_type)
            except ValueError:
                elem.clear()
                continue

            # T016: Compute import hash
            import_hash = compute_import_hash(timestamp, phone_number, body)

            batch.append((
                phone_number,
                contact_name,
                body,
                timestamp,
                message_type,
                import_hash
            ))

            # T017: Batch insert with 1000-record transactions
            if len(batch) >= batch_size:
                result = insert_batch(cursor, batch)
                imported += result['inserted']
                duplicates += result['duplicates']
                batch = []
                conn.commit()

                # T018: Progress output
                processed = imported + duplicates
                pct = (processed / total * 100) if total > 0 else 0
                print(f"Progress: {processed:,} / {total:,} ({pct:.1f}%)")

            # T019: Clear element after processing to bound memory
            elem.clear()

        # Insert remaining batch
        if batch:
            result = insert_batch(cursor, batch)
            imported += result['inserted']
            duplicates += result['duplicates']
            conn.commit()

        conn.close()
        return imported, duplicates, None

    except Exception as e:
        # T020: Error handling for malformed XML
        conn.close()
        return imported, duplicates, str(e)


def insert_batch(cursor, batch):
    """Insert batch of messages, handling duplicates via INSERT OR IGNORE."""
    inserted = 0
    duplicates = 0

    for record in batch:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO messages
                (phone_number, contact_name, body, timestamp, message_type, import_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', record)

            if cursor.rowcount > 0:
                inserted += 1
            else:
                duplicates += 1
        except Exception:
            duplicates += 1

    return {'inserted': inserted, 'duplicates': duplicates}


def main():
    # T013: CLI argument parsing
    parser = argparse.ArgumentParser(
        description='Import SMS Backup & Restore XML files into Retext database',
        epilog='Example: python import_sms.py backup.xml'
    )
    parser.add_argument(
        'file',
        help='Path to SMS Backup & Restore XML file'
    )

    args = parser.parse_args()

    print(f"Importing: {args.file}")
    start_time = time.time()

    imported, duplicates, error = import_xml(args.file)

    elapsed = time.time() - start_time

    if error:
        # T020: Clear error message
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    # T021: Import summary
    print(f"\nComplete: {imported:,} messages imported ({duplicates:,} duplicates skipped)")
    print(f"Time: {elapsed:.1f} seconds")

    sys.exit(0)


if __name__ == '__main__':
    main()
