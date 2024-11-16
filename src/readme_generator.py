from pathlib import Path
from typing import List, Dict, Optional, Union
import openai
import yaml

class ReadmeGenerator:
    """
    Generates repository documentation by analyzing code structure.
    
    Handles:
    - Repository analysis
    - Language detection
    - Documentation generation using OpenAI
    - Configuration management
    """
    
    def __init__(self) -> None:
        """
        Initialize generator with configuration from YAML files.
        
        Config search order:
        1. ./config/ (development)
        2. ~/.config/read-you/ (user)
        3. /etc/read-you/ (system)
        
        Raises:
            FileNotFoundError: If no config found
            ValueError: If API key invalid/missing
        """
        self.config = self._load_config()
        self.client = self._init_openai()
        
    def _load_config(self) -> Dict:
        """
        Load and merge configuration files.
        
        Returns:
            Dict: Merged configuration
            
        Raises:
            FileNotFoundError: No config found
            ValueError: Invalid YAML or missing required fields
        """
        possible_config_dirs = [
            Path(__file__).parent.parent / 'config',
            Path.home() / '.config' / 'read-you',
            Path('/etc/read-you'),
        ]
        
        config_dir = next(
            (d for d in possible_config_dirs if (d / 'example.yaml').exists()),
            None
        )
        
        if not config_dir:
            config_dir = possible_config_dirs[1]
            config_dir.mkdir(parents=True, exist_ok=True)
            self._copy_default_configs(config_dir)
            
        return self._read_configs(config_dir)
    
    def _copy_default_configs(self, target_dir: Path) -> None:
        """Copy default config files to target directory."""
        package_config = Path(__file__).parent.parent / 'config'
        if package_config.exists():
            import shutil
            shutil.copy2(package_config / 'example.yaml', target_dir / 'example.yaml')
            shutil.copy2(package_config / 'secrets.yaml.template', target_dir / 'secrets.yaml.template')
    
    def _read_configs(self, config_dir: Path) -> Dict:
        """
        Read and merge example.yaml and secrets.yaml.
        
        Args:
            config_dir: Directory containing config files
            
        Returns:
            Dict: Merged configuration
            
        Raises:
            FileNotFoundError: Missing example.yaml
            ValueError: Invalid YAML or missing API key
        """
        try:
            with open(config_dir / 'example.yaml') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration not found in: {[str(d) for d in possible_config_dirs]}"
            )
            
        secrets_path = config_dir / 'secrets.yaml'
        if not secrets_path.exists():
            raise ValueError(
                f"No secrets.yaml found. Create {secrets_path} with your OpenAI API key"
            )
            
        try:
            with open(secrets_path) as f:
                secrets = yaml.safe_load(f)
                self._merge_configs(config, secrets)
        except Exception as e:
            raise ValueError(f"Error reading secrets.yaml: {e}")
            
        return config
    
    def _init_openai(self) -> openai.OpenAI:
        """
        Initialize OpenAI client.
        
        Returns:
            OpenAI client instance
            
        Raises:
            ValueError: Invalid API key
        """
        api_key = self.config['openai'].get('api_key')
        if not api_key or api_key in ["YOUR-API-KEY-GOES-IN-SECRETS.YAML", "your-actual-api-key-here"]:
            raise ValueError("Invalid API key. Add your OpenAI key to secrets.yaml")
            
        self.model = self.config['openai'].get('model', 'gpt-4-0125-preview')
        return openai.OpenAI(api_key=api_key)
    
    def _merge_configs(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
                
    def analyze_directory(self, directory: Path) -> Dict[str, List[str]]:
        """Analyze a directory and collect relevant code files."""
        file_contents = {}
        # Define directories to ignore
        ignore_dirs = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'build', 'dist', '*.egg-info'}
        
        # Common entry points and important files by language
        important_patterns = {
            '.py': ['main.py', 'app.py', 'index.py', 'setup.py'],
            '.js': ['index.js', 'main.js', 'app.js', 'server.js'],
            '.ts': ['index.ts', 'main.ts', 'app.ts', 'server.ts'],
            '.go': ['main.go', 'app.go', 'server.go'],
            '.rs': ['main.rs', 'lib.rs'],
            '.java': ['Main.java', 'App.java', 'Application.java'],
            '.rb': ['main.rb', 'app.rb', 'application.rb'],
            '.php': ['index.php', 'app.php'],
            '.cs': ['Program.cs', 'Startup.cs']
        }

        # First pass: Find all code files and identify primary language
        language_counts = {}
        all_files = []
        for ext in important_patterns.keys():
            files = list(directory.rglob(f'*{ext}'))
            valid_files = []
            for file in files:
                if not any(ignore_dir in str(file) for ignore_dir in ignore_dirs):
                    valid_files.append(file)
            if valid_files:
                language_counts[ext] = len(valid_files)
                all_files.extend(valid_files)

        if not language_counts:
            raise ValueError("No recognized source code files found in the repository")

        # Determine primary language(s)
        max_count = max(language_counts.values())
        primary_languages = [ext for ext, count in language_counts.items() if count >= max_count * 0.3]  # Languages with at least 30% of max files

        # Second pass: Organize and prioritize files
        for ext in primary_languages:
            files_by_importance = []
            
            # 1. First priority: Known entry points in src/ or primary directories
            for pattern in important_patterns[ext]:
                for file in all_files:
                    if file.name == pattern and ext in str(file):
                        if 'src/' in str(file) or 'lib/' in str(file) or 'app/' in str(file):
                            files_by_importance.insert(0, file)
                        else:
                            files_by_importance.append(file)

            # 2. Second priority: Other files in src/ or primary directories
            for file in all_files:
                if ext in str(file) and file not in files_by_importance:
                    if 'src/' in str(file) or 'lib/' in str(file) or 'app/' in str(file):
                        files_by_importance.append(file)

            # 3. Third priority: Remaining files
            for file in all_files:
                if ext in str(file) and file not in files_by_importance:
                    files_by_importance.append(file)

            # Limit to most important files (entry points and core modules)
            files_by_importance = files_by_importance[:5]  # Limit to top 5 most important files

            if files_by_importance:
                file_contents[ext] = []
                for file in files_by_importance:
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            relative_path = file.relative_to(directory)
                            file_contents[ext].append(f"# File: {relative_path}\n{content}")
                    except Exception as e:
                        print(f"Error reading {file}: {e}")

        return file_contents

    def _detect_project_type(self, file_contents: Dict[str, List[str]]) -> str:
        """Detect the primary project type based on files found."""
        if not file_contents:
            return "Unknown"
        
        # Count files by extension
        ext_counts = {ext: len(files) for ext, files in file_contents.items()}
        primary_ext = max(ext_counts, key=ext_counts.get)
        
        # Map extensions to project types
        type_mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#'
        }
        
        return type_mapping.get(primary_ext, "Unknown")

    def generate_readme(self, repo_path: Union[str, Path], verbose: bool = False) -> str:
        """
        Generate README content for repository.
        
        Args:
            repo_path: Path to repository
            verbose: Generate detailed documentation
            
        Returns:
            str: Generated README content
            
        Raises:
            FileNotFoundError: Invalid repository path
            Exception: OpenAI API errors
        """
        directory = Path(repo_path)
        file_contents = self.analyze_directory(directory)
        project_type = self._detect_project_type(file_contents)
        
        footer = f"\n\n---\n*This README was automatically generated using [read-you](https://github.com/yourusername/read-you)*"
        
        # Prepare the prompt for OpenAI
        if verbose:
            prompt = f"""You are analyzing a {project_type} project's source code to generate a README.md file.
            Focus on the most important implementation files, which have been automatically identified and prioritized.
            
            Key points to analyze:
            1. Look for main entry points and core functionality
            2. Identify the project's primary features and purpose
            3. Note any command-line arguments, API endpoints, or configuration options
            4. Identify required dependencies from imports/package files
            
            Files found: {list(file_contents.keys())}
            
            Please include:
            1. Project Title (based on the main functionality)
            2. Clear description of what the code actually does
            3. Installation Instructions (specific to {project_type})
            4. Usage Examples (based on actual implementation)
            5. Project Structure (focusing on key files)
            6. Dependencies (based on actual imports/requirements)
            7. Contributing Guidelines
            8. License Information (if found)
            
            Do not add any footer - it will be added automatically.
            """
        else:
            prompt = f"""You are analyzing a {project_type} project's source code to generate a concise README.md.
            Focus on the most important implementation files that have been automatically identified.
            
            Files found: {list(file_contents.keys())}
            
            Create a brief README focusing on:
            1. What the code actually does (based on the implementation)
            2. How to use it (based on actual code patterns found)
            3. Basic requirements (specific to {project_type})
            
            Be direct and accurate. Only describe functionality that exists in the code.
            Do not add any footer - it will be added automatically.
            """
        
        prompt += "\nHere's the actual code to analyze:\n"
        
        for ext, contents in file_contents.items():
            if contents:
                prompt += f"\n{ext} files:\n"
                for content in contents:
                    prompt += f"{content}\n"

        # Generate README using OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a technical documentation expert specializing in {project_type}. Generate a README.md based ONLY on the actual code provided, not assumptions. Focus on the main implementation files and ignore configuration or build files."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000 if verbose else 1000
        )
        
        return response.choices[0].message.content + footer

    def save_readme(self, repo_path: str, content: str, dry_run: bool = False) -> None:
        """Save the generated README to the repository or print to console if dry_run is True."""
        if dry_run:
            print("\n=== Generated README Content ===\n")
            print(content)
            print("\n============================\n")
        else:
            readme_path = Path(repo_path) / "README.md"
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)