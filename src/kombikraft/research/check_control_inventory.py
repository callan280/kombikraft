"""Exercise recovered CC IDs using matching local banks and original code.

Single-selected-ID fixtures are followed by original clears. This is not a
warning-master, vehicle-transport, GPU, or acknowledgement-lifecycle test.
"""
import argparse
from collections import Counter
import hashlib
from importlib import resources
import json
from pathlib import Path
import re
import struct

from ..factory.worker import SourceControllerProcess


def catalogue():
    raw = resources.files('kombikraft').joinpath('factory', 'cc_inventory_profile.json').read_bytes()
    value = json.loads(raw)
    if value.get('schema') != 'original-cc-id-inventory-v1' or value.get('sourceProfile') != 'gss-5c58-160.002.002':
        raise ValueError('Unsupported original CC inventory')
    entries = value['entries']
    ids = [r['ccid'] for r in entries]
    if len(entries) != 966 or ids != sorted(set(ids)) or any(type(x) is not int or not 0 <= x <= 65535 for x in ids):
        raise ValueError('Incomplete recovered CC-ID inventory')
    return value, hashlib.sha256(raw).hexdigest()


def validate_selection(result, ccid):
    """Check actual committed output, including a true null-pointer clear."""
    selected = result['selected']
    for key in ('selectedCcid', 'sourceLanguageOrdinal', 'sourceVariantIndex', 'sourceCollectionBankOrdinal'):
        if type(selected.get(key)) is not int:
            raise ValueError('Expected exact original integer source ordinals')
    if selected.get('selectedCcid') != ccid or selected.get('payloadReadbackMatchesConsumer') is not True:
        raise ValueError('Original selected ID or committed-payload readback differs')
    if (selected.get('sourceProfile'), selected.get('sourceLanguageOrdinal'), selected.get('sourceVariantIndex'),
            selected.get('sourceCollectionBankOrdinal')) != ('gss-5c58-160.002.002', 2, 1, 1):
        raise ValueError('Original source configuration differs from the reviewed fixture')
    if ccid and selected.get('originalPayloadConsumerObserved') is not True:
        raise ValueError('Original registered widget did not observe a payload')
    if selected.get('originalGraphicsReady') is not False:
        raise ValueError('Unexpected original graphics state')
    if ccid == 0:
        payload = bytes.fromhex(selected['sourcePayload72Hex'])
        if len(payload) != 72 or any(struct.unpack_from('<Q', payload, off)[0] for off in (0, 8, 16, 32)):
            raise ValueError('Original clear retains text/icon pointers')
        if (selected.get('textLines'), selected.get('primaryIcon'), selected.get('collectionSlots'),
                selected.get('iconSelector'), selected.get('textSelector')) != ([None, None], None, [], 255, 255):
            raise ValueError('Original clear retains display content')
    return selected


def run(manifest, root, output, ids=None):
    inventory, inventory_sha = catalogue()
    by_id = {r['ccid']: r for r in inventory['entries']}
    if ids is None:
        ids = list(by_id)
    if not ids or len(ids) != len(set(ids)) or any(type(i) is not int or i not in by_id for i in ids):
        raise ValueError('Choose distinct IDs from the recovered original inventory')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows_path = output / 'cases.ndjson'
    counts = Counter()
    comparisons = Counter()
    completed = 0
    package = Path(__file__).resolve().parents[1]
    implementation_paths = [Path(__file__), *(package / 'factory' / name for name in
        ('worker.py', 'backend.py', 'check_control.py', 'inputs.py', 'platform.py', 'profile.py', 'cc_inventory_profile.json'))]
    implementation = {str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in implementation_paths}
    final = {'schema': 'original-cc-id-inventory-execution-v1', 'passed': False, 'executionCompleted': False,
             'inventorySha256': inventory_sha, 'requestedIds': ids, 'recoveredInventoryCount': 966,
             'fullRecoveredInventoryRequested': set(ids) == set(by_id),
             'configuration': {'sourceLanguageOrdinalExplicitFixture': 2, 'untouchedVariantAndBankDefaults': [1, 1]},
             'inputKind': 'authored-single-selected-id-internal-fixtures-with-original-clear-after-each',
             'sourceExecutionModel': 'isolated-process-main-thread', 'allPossibleU16IdsCovered': False,
             'implementationSha256': implementation,
             'masterArbitrationVerified': False, 'acknowledgementPersistenceVerified': False,
             'factoryGraphicsRendered': False, 'physicalTransportVerified': False,
             'currentCarCompatibilityVerified': False, 'installationAllowed': False}
    try:
        with SourceControllerProcess(manifest, root, check_control=True) as backend, rows_path.open('x') as sink:
            final['initialStatus'] = backend.status()
            for ccid in ids:
                result = backend.receive('checkControl', {'ccid': ccid})
                selected = validate_selection(result, ccid)
                clear = backend.receive('checkControl', {'ccid': 0})
                validate_selection(clear, 0)
                category = ('clear' if ccid == 0 else 'collection' if selected['collectionSlots'] else
                            'primary-icon' if selected['primaryIcon'] else 'text-only' if any(selected['textLines']) else
                            'empty-selection')
                templates = by_id[ccid]['originalTextTemplates']
                # Runtime formatting is observed, never recreated by this tool.
                comparison = ('clear-not-text-template' if ccid == 0 else 'exact' if selected['textLines'] == templates else
                              'runtime-placeholder-output' if any(re.search(r'%[0-9]', text or '') for text in templates) else
                              'unexplained-template-difference')
                comparisons[comparison] += 1
                counts[category] += 1
                row = {'ccid': ccid, 'recordIndex': by_id[ccid]['recordIndex'], 'category': category,
                       'originalTextTemplates': templates, 'templateComparison': comparison,
                       'result': result, 'clear': clear}
                sink.write(json.dumps(row, separators=(',', ':')) + '\n')
                sink.flush()
                completed += 1
                if comparison == 'unexplained-template-difference':
                    raise ValueError('Original output differs from a fixed text template')
            final['finalStatus'] = backend.status()
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != implementation[str(path.relative_to(package))]
               for path in implementation_paths):
            raise ValueError('Source implementation changed while the experiment was running')
        final.update(passed=True, executionCompleted=True)
    except Exception as exc:
        final['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        final.update(completedIds=completed, categoryCounts=dict(counts), templateComparisons=dict(comparisons),
                     casesSha256=hashlib.sha256(rows_path.read_bytes()).hexdigest() if rows_path.exists() else None)
        with (output / 'receipt.json').open('x') as stream:
            stream.write(json.dumps(final, indent=2) + '\n')
    return final


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalogue', action='store_true', help='Print inventory metadata; no source execution')
    p.add_argument('--manifest', type=Path, help='Exact supported 14-bank source manifest')
    p.add_argument('--root', type=Path, help='Local matching source-bank directory')
    p.add_argument('--output', type=Path, help='New directory for source observations and receipt')
    p.add_argument('--ids', type=int, nargs='+', help='Explicit inventory subset; default exercises all966 recovered IDs')
    args = p.parse_args(argv)
    if args.catalogue:
        inventory, digest = catalogue()
        print(json.dumps({k: v for k, v in inventory.items() if k != 'entries'} | {'inventorySha256': digest}, indent=2))
        return 0
    if not all((args.manifest, args.root, args.output)):
        p.error('Supply --manifest, --root and --output, or use --catalogue')
    try:
        result = run(args.manifest, args.root, args.output, args.ids)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        p.exit(1, f'Original CC inventory execution failed: {exc}\n')
    print(json.dumps({k: result[k] for k in ('passed', 'completedIds', 'categoryCounts', 'templateComparisons',
                                          'fullRecoveredInventoryRequested', 'casesSha256')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
