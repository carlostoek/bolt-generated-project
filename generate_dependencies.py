# generate_dependencies.py
import pydeps.cli
from pathlib import Path

def generate_dependency_map():
    targets = [
        'src/core',
        'src/services',
        'src/utils'
    ]
    for target in targets:
        pydeps.cli.run([
            str(Path(target)),
            '--show-dot',
            '--output', f'docs/{Path(target).name}_dependencies.svg',
            '--max-bacon=2'  # Profundidad de relaciones
        ])

if __name__ == '__main__':
    generate_dependency_map()
