#!/usr/bin/env python3
"""Reconstruct this prepared source snapshot offline. No network or provider."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys, tempfile
def sha(data): return hashlib.sha256(data).hexdigest()
def run(bundle, destination):
    metadata = json.loads((bundle / 'SOURCE_SNAPSHOT_V14.json').read_text())
    expected = metadata['source_file_hashes']
    modes = metadata['source_file_modes']
    if not isinstance(expected, dict) or len(expected) != metadata['source_files'] or set(modes) != set(expected):
        raise ValueError('Invalid source inventory')
    for name, checksum in expected.items():
        p = Path(name)
        if not name or p.is_absolute() or '..' in p.parts or chr(92) in name or p.as_posix() != name or not re.fullmatch('[a-f0-9]{64}', checksum) or modes[name] not in ['100644', '100755']:
            raise ValueError('Invalid source path, hash or mode')
    if metadata['patch'] != 'hosted-v14.patch': raise ValueError('Unexpected patch path')
    patch = bundle / metadata['patch']; data = patch.read_bytes()
    if sha(data) != metadata['patch_sha256'] or len(data) != metadata['patch_bytes']: raise ValueError('Patch hash or size mismatch')
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink(): raise ValueError('Destination exists; choose a new directory')
    with tempfile.TemporaryDirectory(prefix='.tastebridge-reproduce-', dir=destination.parent) as temp:
        stage = Path(temp) / 'source'; stage.mkdir()
        cmd = ['git', 'apply', '--no-index', '-p0']
        subprocess.run(cmd + ['--check', str(patch)], cwd=stage, check=True)
        subprocess.run(cmd + [str(patch)], cwd=stage, check=True)
        hosted = stage / 'hosted'
        actual_paths = {p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
        if actual_paths != {'hosted/' + name for name in expected}: raise ValueError('Unexpected files outside source inventory')
        if any(p.is_symlink() for p in stage.rglob('*')): raise ValueError('Unexpected source symlink')
        inventory = {p.relative_to(hosted).as_posix(): sha(p.read_bytes()) for p in hosted.rglob('*') if p.is_file()}
        if inventory != expected: raise ValueError('Source inventory mismatch')
        if any(format(0o100755 if (hosted/n).stat().st_mode & 0o111 else 0o100644, 'o') != modes[n] for n in expected): raise ValueError('Source mode mismatch')
        subprocess.run(['git', 'init', '--quiet'], cwd=stage, check=True)
        subprocess.run(['git', 'add', '--force', '--'] + ['hosted/' + n for n in sorted(expected)], cwd=stage, check=True)
        subprocess.run([sys.executable, 'scripts/export_public_source.py'], cwd=hosted, check=True)
        archive = (hosted/'public/source/TasteBridge-source.zip').read_bytes()
        manifest = (hosted/'public/source/source-manifest.json').read_bytes()
        if sha(archive) != metadata['source_zip_sha256'] or len(archive) != metadata['source_zip_bytes'] or sha(manifest) != metadata['public_manifest_sha256']: raise ValueError('Regenerated distribution mismatch')
        stage.rename(destination)
    return {'status':'PASS','target_version':metadata['target_version'],'publication_state':'PREPARED_NOT_PROVEN_DEPLOYED','source_files':len(expected),'source_zip_sha256':sha(archive),'network_calls':0,'provider_calls':0}
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,default=Path('reproduced-v14')); args=parser.parse_args()
    try: result=run(Path(__file__).resolve().parent,args.output)
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as error: parser.exit(1,'Reconstruction failed: '+str(error)+'\n')
    print(json.dumps(result,indent=2))
