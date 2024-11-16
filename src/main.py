"""
Automatic README generator for code repositories
"""
import argparse
from pathlib import Path
from .readme_generator import ReadmeGenerator

def main():
    parser = argparse.ArgumentParser(
        description="Generate README files from repository analysis"
    )
    parser.add_argument(
        "repo_path",
        type=str,
        help="Repository path to analyze"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="OpenAI model to use (default: from config)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Generate detailed README"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview without creating file"
    )
    
    args = parser.parse_args()
    
    try:
        generator = ReadmeGenerator()
        content = generator.generate_readme(
            args.repo_path,
            model=args.model,
            verbose=args.verbose
        )
        
        if args.dry_run:
            print(content)
            return 0
            
        readme_path = Path(args.repo_path) / "README.md"
        with open(readme_path, "w") as f:
            f.write(content)
        print(f"README generated at: {readme_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())