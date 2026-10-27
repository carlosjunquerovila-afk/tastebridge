#!/usr/bin/env python3
"""Reconstruct verified TasteBridge v13 locally. No network, keys or paid calls."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_tree(hosted, manifest):
    files = {p.relative_to(hosted).as_posix(): digest(p.read_bytes())
             for p in hosted.rglob('*') if p.is_file()}
    if any(p.is_symlink() for p in hosted.rglob('*')):
        raise ValueError('Unexpected symlink in reconstructed source')
    if files != manifest['source_file_hashes']:
        raise ValueError('Reconstructed source inventory or hashes differ')


def reproduce(bundle, destination):
    bundle = bundle.resolve()
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination already exists; choose a new directory')
    manifest = json.loads((bundle / 'SOURCE_SNAPSHOT_V13.json').read_text())
    if manifest['version'] != 13 or manifest['patch'] != 'hosted-v13.patch':
        raise ValueError('Unexpected snapshot format')
    expected = manifest['source_file_hashes']
    if not isinstance(expected, dict) or len(expected) != manifest['source_files']:
        raise ValueError('Invalid source inventory')
    for name, checksum in expected.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or not name or len(checksum) != 64:
            raise ValueError('Invalid source path or checksum')
    patch = bundle / manifest['patch']
    data = patch.read_bytes()
    if len(data) != manifest['patch_bytes'] or digest(data) != manifest['patch_sha256']:
        raise ValueError('Patch hash/size differs; refusing to apply')
    # A private temporary tree avoids leaving a half-created destination.
    with tempfile.TemporaryDirectory(prefix='.tastebridge-v13-', dir=destination.parent) as temp:
        stage = Path(temp) / 'reconstructed'
        stage.mkdir()
        command = ['git', 'apply', '--no-index', '-p0']
        subprocess.run(command + ['--check', str(patch)], cwd=stage, check=True)
        subprocess.run(command + [str(patch)], cwd=stage, check=True)
        hosted = stage / 'hosted'
        verify_tree(hosted, manifest)
        # The exporter intentionally enumerates Git source, not installed or
        # private runtime files. This is an isolated local repository, no remote.
        subprocess.run(['git', 'init', '--quiet'], cwd=stage, check=True)
        subprocess.run(['git', 'add', '--force', '--'] + ['hosted/' + n for n in sorted(expected)], cwd=stage, check=True)
        subprocess.run([sys.executable, 'scripts/export_public_source.py'], cwd=hosted, check=True)
        generated = json.loads((hosted / 'public/source/source-manifest.json').read_text())
        archive = (hosted / 'public/source/TasteBridge-source.zip').read_bytes()
        if generated['source_file_hashes'] != expected or digest(archive) != manifest['source_zip_sha256'] or len(archive) != manifest['source_zip_bytes']:
            raise ValueError('Generated public distribution differs from deployed source')
        stage.rename(destination)
    return {'status': 'PASS', 'version': 13, 'source_files': len(expected),
            'canonical_commit': manifest['canonical_commit'],
            'destination': str(destination), 'source_zip_sha256': digest(archive),
            'network_calls': 0, 'provider_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('reproduced-v13'))
    args = parser.parse_args()
    try:
        result = reproduce(Path(__file__).resolve().parent, args.output)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, 'Reconstruction failed: ' + str(error) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
