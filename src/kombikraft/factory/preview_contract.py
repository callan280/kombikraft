"""Admit exact original CC output to the existing custom browser composition.

The contract contains source identity/visual metadata, never firmware code.
No vehicle transport, VM startup or warning-master policy is implemented here.
"""
from copy import deepcopy
from importlib import resources
import hashlib
import json
import math
import struct

from ..assets import AssetError


class PreviewContractError(ValueError):
    pass


class SourceCcPreviewContract:
    def __init__(self, asset_pack=None):
        raw = resources.files('kombikraft').joinpath('factory', 'cc_preview_contract.json').read_bytes()
        self.contract_sha256 = hashlib.sha256(raw).hexdigest()
        self.contract = json.loads(raw)
        if self.contract.get('schema') != 'gss-to-canvas-cc-asset-contract-v1':
            raise PreviewContractError('Unsupported source-output asset contract')
        self.expected = {row['ccid']: row for row in self.contract['records']}
        if len(self.expected) != 16 or self.contract['sourceProfile'] != 'gss-5c58-160.002.002':
            raise PreviewContractError('Incomplete source-output asset contract')
        self.configurations = {(c['languageOrdinal'], c['variantIndex'], c['collectionBankOrdinal'])
                               for c in self.contract['reviewedConfigurations']}
        if self.configurations != {(2, 0, 0), (2, 1, 1)}:
            raise PreviewContractError('Unreviewed source-output configuration')
        self.assets = asset_pack

    def _verify_assets(self):
        if self.assets is None:
            raise PreviewContractError('The reviewed local visual pack is not loaded')
        for route, expected in self.contract['assetRoutes'].items():
            content = self.assets.read(route)
            if hashlib.sha256(content).hexdigest() != expected:
                raise PreviewContractError('Visual pack differs from the reviewed warning assets')

    def status(self):
        result = {'available': False, 'kind': 'original-output-to-custom-canvas',
                  'assetContractSha256': self.contract_sha256, 'supportedPopupCount': 16,
                  'customComposition': True, 'factoryGraphics': False,
                  'physicalTransport': False, 'vehicleCompatibilityVerified': False}
        try:
            self._verify_assets()
            result['available'] = True
        except (AssetError, PreviewContractError, OSError, KeyError, TypeError, ValueError) as exc:
            result['reason'] = str(exc)
        return result

    def _selection(self, selected):
        if not isinstance(selected, dict) or selected.get('sourceProfile') != self.contract['sourceProfile']:
            raise PreviewContractError('Source profile differs from the reviewed warning assets')
        if selected.get('originalPayloadConsumerObserved') is not True or selected.get('payloadReadbackMatchesConsumer') is not True:
            raise PreviewContractError('The original widget has not received a matching committed payload')
        if selected.get('originalGraphicsReady') is not False:
            raise PreviewContractError('Source graphics state is outside the reviewed offline fixture')
        keys = ('sourceLanguageOrdinal', 'sourceVariantIndex', 'sourceCollectionBankOrdinal')
        if any(type(selected.get(k)) is not int for k in keys) or tuple(selected[k] for k in keys) not in self.configurations:
            raise PreviewContractError('Source language/configuration has no matching asset contract')
        ccid = selected.get('selectedCcid')
        if type(ccid) is not int or not 0 <= ccid <= 65535:
            raise PreviewContractError('The original selected CCID must be UInt16')
        record = bytes.fromhex(selected['selectedRecord64Hex'])
        payload = bytes.fromhex(selected['sourcePayload72Hex'])
        if len(record) != 64 or len(payload) != 72 or struct.unpack_from('<H', record)[0] != ccid:
            raise PreviewContractError('Original request/payload identity mismatch')
        for key in ('iconSelector', 'textSelector'):
            if type(selected.get(key)) is not int or not 0 <= selected[key] <= 255:
                raise PreviewContractError('Invalid original selector readback')
        if (selected['iconSelector'], selected['textSelector']) != (payload[66], payload[64]):
            raise PreviewContractError('Original selectors differ from the committed payload')
        for key in ('iconSelectorHelperRGBA', 'textSelectorHelperRGBA'):
            value = selected.get(key)
            if not isinstance(value, list) or len(value) != 4 or any(
                    type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1 for x in value):
                raise PreviewContractError('Invalid original palette readback')
        lines = selected.get('textLines')
        if not isinstance(lines, list) or len(lines) != 2 or any(x is not None and not isinstance(x, str) for x in lines):
            raise PreviewContractError('Expected two original nullable text lines')
        if not isinstance(selected.get('collectionSlots'), list):
            raise PreviewContractError('Expected original collection slot readback')
        if selected['collectionSlots'] or struct.unpack_from('<Q', payload, 32)[0]:
            raise PreviewContractError('The current canvas adapter does not render collection warnings')
        if ccid == 0:
            if lines != [None, None] or selected.get('primaryIcon') is not None or any(
                    struct.unpack_from('<Q', payload, off)[0] for off in (0, 8, 16, 32)):
                raise PreviewContractError('Original clear still contains text or icon pointers')
            if (selected['iconSelector'], selected['textSelector']) != (255, 255) or any(
                    selected[k] != [1, 1, 1, 1] for k in ('iconSelectorHelperRGBA', 'textSelectorHelperRGBA')):
                raise PreviewContractError('Original clear selectors/palette are unreviewed')
            return ccid, None
        expected = self.expected.get(ccid)
        if expected is None:
            raise PreviewContractError('No reviewed canvas assets for this original selected CCID')
        for key in ('textLines', 'iconSelector', 'textSelector', 'iconSelectorHelperRGBA', 'textSelectorHelperRGBA'):
            if selected[key] != expected[key]:
                raise PreviewContractError('Original output differs from the reviewed warning assets: ' + key)
        icon = selected.get('primaryIcon')
        if not isinstance(icon, dict) or icon.get('sourceProfile') != self.contract['sourceProfile']:
            raise PreviewContractError('Original primary icon has no matching source identity')
        for key, value in expected['primaryIcon'].items():
            if icon.get(key) != value or type(icon[key]) is not type(value):
                raise PreviewContractError('Original primary icon differs from the reviewed asset: ' + key)
        if struct.unpack_from('<Q', payload, 16)[0] != int(icon['descriptorVa'], 16):
            raise PreviewContractError('Original icon does not match the committed payload')
        return ccid, expected

    def plan(self, selected):
        result = {'schema': 'original-cc-custom-canvas-plan-v1', 'status': 'unsupported',
                  'action': None, 'popup': None, 'sourceProfile': self.contract['sourceProfile'],
                  'assetContractSha256': self.contract_sha256, 'originalControllerComputed': True,
                  'customComposition': True, 'factoryGraphics': False,
                  'warningMasterArbitrationVerified': False, 'physicalTransport': False,
                  'vehicleCompatibilityVerified': False, 'installationAllowed': False}
        try:
            self._verify_assets()
            ccid, expected = self._selection(selected)
            result.update(status='supported', action='clear' if ccid == 0 else 'show', selectedCcid=ccid)
            if expected is not None:
                popup = deepcopy(expected['popup'])
                popup.update(originalCcFixture=True, originalControllerComputed=True,
                             placementFixture=False, customComposition=True,
                             sourceProfile=self.contract['sourceProfile'])
                result['popup'] = popup
        except (AssetError, PreviewContractError, OSError, KeyError, TypeError, ValueError, struct.error) as exc:
            result['reason'] = str(exc)
        return result
