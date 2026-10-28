"""Digital invoice review: deterministic MOCK extraction, not an AI call."""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
import re

ALIASES = {'invoice':['Invoice','Invoice number'], 'date':['Date','Issue date'],
           'subtotal':['Subtotal','Net amount'], 'tax':['Tax','Tax amount'],
           'total':['Total','Amount due'], 'currency':['Currency']}
FIELDS = list(ALIASES)+['source_page']


def parse_mock(pages):
    result = {key:'' for key in FIELDS}
    matched_pages = set()
    for page_number, text in enumerate(pages, 1):
        for line in text.splitlines():
            for key, labels in ALIASES.items():
                for label in labels:
                    match = re.fullmatch(re.escape(label)+r'\s*[:|]\s*(.+)', line.strip())
                    if match:
                        if result[key]: raise ValueError('Ambiguous duplicate field: '+key)
                        result[key]=match.group(1).strip()
                        matched_pages.add(page_number)
    if len(matched_pages)>1: raise ValueError('Demo supports one invoice page only')
    result['source_page']=str(next(iter(matched_pages))) if matched_pages else ''
    return result


def validate(fields):
    errors=[]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,39}',fields.get('invoice','')):
        errors.append('Invoice ID must use letters, digits, underscores or hyphens')
    try:
        value=fields.get('date','')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value): raise ValueError()
        date.fromisoformat(value)
    except ValueError: errors.append('Invalid date')
    amounts={}
    for key in ['subtotal','tax','total']:
        value=fields.get(key,'')
        if not re.fullmatch(r'\d{1,9}\.\d{2}',value): errors.append('Invalid '+key+' (use nonnegative decimal with 2 places)')
        else: amounts[key]=Decimal(value)
    if len(amounts)==3 and amounts['subtotal']+amounts['tax']!=amounts['total']:
        errors.append('Subtotal plus tax must equal total')
    if fields.get('currency') not in ['USD','EUR','GBP']: errors.append('Currency must be USD, EUR or GBP')
    if not re.fullmatch(r'[1-9]\d*',fields.get('source_page','')): errors.append('Missing source page')
    return errors


MAX_PDF_BYTES = 2*1024*1024


def read_snapshot(path):
    """Read once, bounded; parsing and provenance share these immutable bytes."""
    with path.open('rb') as stream:
        snapshot = stream.read(MAX_PDF_BYTES + 1)
    if len(snapshot) > MAX_PDF_BYTES: raise ValueError('PDF exceeds 2 MiB')
    return snapshot


def extract_pdf(path):
    return extract_snapshot(read_snapshot(path))


def extract_snapshot(snapshot):
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError
    if len(snapshot) > MAX_PDF_BYTES: raise ValueError('PDF exceeds 2 MiB')
    try:
        reader=PdfReader(io.BytesIO(snapshot))
        if reader.is_encrypted or len(reader.pages)>2: raise ValueError('Use an unencrypted PDF with at most 2 pages')
        pages=[page.extract_text() or '' for page in reader.pages]
    except PyPdfError as exc:
        raise ValueError('Unreadable PDF') from exc
    if not any(text.strip() for text in pages): raise ValueError('No digital text; OCR is not supported')
    return pages


def export_csv(fields, source, sha256, approved):
    if not approved: raise ValueError('Explicit human approval required')
    errors=validate(fields)
    if errors: raise ValueError('; '.join(errors))
    # Source metadata may be arbitrary filenames; neutralize spreadsheet prefixes.
    source="'"+source if source.startswith(('=','+','-','@','\t','\r')) else source
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=FIELDS+['source_file','source_sha256','extraction_mode','review_status'],lineterminator='\n')
    writer.writeheader(); writer.writerow({**{key:fields[key] for key in FIELDS},'source_file':source,'source_sha256':sha256,'extraction_mode':'mock_rules','review_status':'human_approved'})
    return stream.getvalue()


def publish(destination, payload):
    """Publish a closed, complete file using an atomic, no-clobber hard link.

    Requires a stable, trusted directory on a local filesystem supporting links.
    This provides visibility atomicity, not power-loss durability.
    """
    staged = tempfile.NamedTemporaryFile(mode='wb', prefix='.csv-json-',
                                         suffix='.tmp', dir=destination.parent,
                                         delete=False)
    temporary = Path(staged.name)
    published = False
    try:
        with staged as stream:
            if stream.write(payload) != len(payload):
                raise OSError('short write while staging output')
            stream.flush()
            os.fsync(stream.fileno())
        # No check-then-rename race: link fails if any destination entry exists,
        # including a dangling symlink. Never remove or replace that entry.
        os.link(temporary, destination)
        published = True
    finally:
        try:
            temporary.unlink()
        except OSError as exc:
            state = 'complete destination was published' if published else 'destination was not published'
            raise OSError(f'temporary cleanup failed: {temporary}; {state}; {exc}') from exc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,default=Path('reviewed.csv'))
    args=parser.parse_args()
    try:
        snapshot=read_snapshot(args.source)
        pages=extract_snapshot(snapshot); fields=parse_mock(pages)
        digest=hashlib.sha256(snapshot).hexdigest()
        print('MOCK EXTRACTION — no AI provider connected. Source:',args.source)
        print('\n'.join(pages))
        for key in ALIASES:
            value=input(f'{key} [{fields[key]}] (Enter keeps value): ').strip()
            if value: fields[key]=value
        errors=validate(fields)
        if errors: raise ValueError('; '.join(errors))
        print(json.dumps(fields,indent=2))
        approved=input('After checking the source, type APPROVE to export: ')=='APPROVE'
        output=export_csv(fields,args.source.name,digest,approved)
        publish(args.output, output.encode('utf-8'))
        print('Saved',args.output)
    except (ValueError,OSError,EOFError) as exc:
        print('error:',exc); return 2
    return 0
if __name__=='__main__': raise SystemExit(main())
