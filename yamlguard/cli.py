"""
Command-line interface for YAMLGuard.

Provides comprehensive CLI with typer and rich output formatting
for all YAMLGuard functionality including linting, validation, and secrets scanning.
"""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from yamlguard.config import Config
from yamlguard.core import YAMLGuard
from yamlguard.reporters import Reporter, StylishReporter, JSONLReporter

# Initialize CLI app
app = typer.Typer(
    name="yamlguard",
    help="Fast, accurate CLI for YAML indentation and Kubernetes manifest validation",
    add_completion=False,
    rich_markup_mode="rich"
)

# Initialize console
console = Console()


@app.command()
def lint(
    paths: List[Path] = typer.Argument(..., help="Files or directories to lint"),
    indent: int = typer.Option(2, "--indent", "-i", help="Indentation step size"),
    strict: bool = typer.Option(False, "--strict", help="Enable strict mode"),
    fix: bool = typer.Option(False, "--fix", help="Auto-fix indentation issues"),
    format: str = typer.Option("stylish", "--format", "-f", help="Output format (stylish, json, jsonl)"),
    color: bool = typer.Option(True, "--color/--no-color", help="Enable/disable colored output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
) -> None:
    """Lint YAML files for indentation and style issues."""
    try:
        # Load configuration
        if config:
            cfg = Config.from_file(config)
        else:
            cfg = Config.find_config() or Config()
        
        # Override config with CLI options
        cfg.indent.step = indent
        cfg.indent.strict = strict
        cfg.indent.fix = fix
        cfg.reporter.format = format
        cfg.reporter.color = color
        cfg.reporter.verbose = verbose
        
        # Initialize YAMLGuard
        yamlguard = YAMLGuard(config=cfg)
        
        # Run linting
        results = yamlguard.lint_files(paths)
        
        # Generate report
        reporter = _get_reporter(cfg)
        report = reporter.report(results)
        
        # Output report
        if format == "json" or format == "jsonl":
            print(report)
        else:
            console.print(report)
        
        # Exit with appropriate code
        if any(not result.get('success', True) for result in results):
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def kube_validate(
    paths: List[Path] = typer.Argument(..., help="Files or directories to validate"),
    version: str = typer.Option("1.30", "--kube-version", "-k", help="Kubernetes version to validate against"),
    strict: bool = typer.Option(False, "--strict", help="Enable strict validation mode"),
    use_kubeconform: bool = typer.Option(True, "--kubeconform/--no-kubeconform", help="Use kubeconform for validation"),
    format: str = typer.Option("stylish", "--format", "-f", help="Output format (stylish, json, jsonl)"),
    color: bool = typer.Option(True, "--color/--no-color", help="Enable/disable colored output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
) -> None:
    """Validate Kubernetes manifests against official schemas."""
    try:
        # Load configuration
        if config:
            cfg = Config.from_file(config)
        else:
            cfg = Config.find_config() or Config()
        
        # Override config with CLI options
        cfg.kubernetes.version = version
        cfg.kubernetes.strict = strict
        cfg.kubernetes.use_kubeconform = use_kubeconform
        cfg.reporter.format = format
        cfg.reporter.color = color
        cfg.reporter.verbose = verbose
        
        # Initialize YAMLGuard
        yamlguard = YAMLGuard(config=cfg)
        
        # Run validation
        results = yamlguard.kube_validate_files(paths)
        
        # Generate report
        reporter = _get_reporter(cfg)
        report = reporter.report(results)
        
        # Output report
        if format == "json" or format == "jsonl":
            print(report)
        else:
            console.print(report)
        
        # Exit with appropriate code
        if any(not result.get('success', True) for result in results):
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def scan_secrets(
    paths: List[Path] = typer.Argument(..., help="Files or directories to scan"),
    baseline: Optional[Path] = typer.Option(None, "--baseline", "-b", help="Baseline file for known secrets"),
    entropy_threshold: float = typer.Option(4.5, "--entropy", "-e", help="Entropy threshold for detection"),
    use_detect_secrets: bool = typer.Option(False, "--detect-secrets", help="Use detect-secrets library"),
    use_gitleaks: bool = typer.Option(False, "--gitleaks", help="Use gitleaks binary"),
    format: str = typer.Option("stylish", "--format", "-f", help="Output format (stylish, json, jsonl)"),
    color: bool = typer.Option(True, "--color/--no-color", help="Enable/disable colored output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
) -> None:
    """Scan YAML files for secrets and credentials."""
    try:
        # Load configuration
        if config:
            cfg = Config.from_file(config)
        else:
            cfg = Config.find_config() or Config()
        
        # Override config with CLI options
        cfg.secrets.baseline = baseline
        cfg.secrets.entropy_threshold = entropy_threshold
        cfg.secrets.use_detect_secrets = use_detect_secrets
        cfg.secrets.use_gitleaks = use_gitleaks
        cfg.reporter.format = format
        cfg.reporter.color = color
        cfg.reporter.verbose = verbose
        
        # Initialize YAMLGuard
        yamlguard = YAMLGuard(config=cfg)
        
        # Run secrets scanning
        results = yamlguard.scan_secrets_files(paths)
        
        # Generate report
        reporter = _get_reporter(cfg)
        report = reporter.report(results)
        
        # Output report
        if format == "json" or format == "jsonl":
            print(report)
        else:
            console.print(report)
        
        # Exit with appropriate code
        if any(not result.get('success', True) for result in results):
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def fix(
    paths: List[Path] = typer.Argument(..., help="Files or directories to fix"),
    indent: int = typer.Option(2, "--indent", "-i", help="Indentation step size"),
    in_place: bool = typer.Option(False, "--in-place", help="Modify files in place"),
    backup: bool = typer.Option(False, "--backup", help="Create backup files"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path")
) -> None:
    """Fix indentation issues in YAML files."""
    try:
        # Load configuration
        if config:
            cfg = Config.from_file(config)
        else:
            cfg = Config.find_config() or Config()
        
        # Override config with CLI options
        cfg.indent.step = indent
        
        # Initialize YAMLGuard
        yamlguard = YAMLGuard(config=cfg)
        
        # Run fixing
        results = yamlguard.fix_files(paths, in_place=in_place, backup=backup)
        
        # Output results
        for result in results:
            if result['success']:
                console.print(f"[green]✅ Fixed: {result['file']}[/green]")
            else:
                console.print(f"[red]❌ Failed: {result['file']} - {result['error']}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def init(
    path: Path = typer.Argument(Path.cwd(), help="Directory to initialize"),
    indent: int = typer.Option(2, "--indent", "-i", help="Default indentation step size"),
    kube_version: str = typer.Option("1.30", "--kube-version", "-k", help="Default Kubernetes version"),
    format: str = typer.Option("stylish", "--format", "-f", help="Default output format")
) -> None:
    """Initialize YAMLGuard configuration in a directory."""
    try:
        # Create configuration
        cfg = Config()
        cfg.indent.step = indent
        cfg.kubernetes.version = kube_version
        cfg.reporter.format = format
        
        # Save configuration
        config_file = path / ".yamlguard.yml"
        cfg.save(config_file)
        
        console.print(f"[green]✅ Created configuration file: {config_file}[/green]")
        
        # Show configuration
        console.print("\n[bold]Configuration:[/bold]")
        console.print(f"  Indentation step: {cfg.indent.step}")
        console.print(f"  Kubernetes version: {cfg.kubernetes.version}")
        console.print(f"  Output format: {cfg.reporter.format}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show YAMLGuard version information."""
    try:
        from yamlguard import __version__
        
        console.print(f"[bold blue]YAMLGuard v{__version__}[/bold blue]")
        console.print("Fast, accurate CLI for YAML indentation and Kubernetes manifest validation")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _get_reporter(config: Config) -> Reporter:
    """Get appropriate reporter based on configuration."""
    if config.reporter.format == "jsonl":
        return JSONLReporter(color=config.reporter.color, verbose=config.reporter.verbose)
    else:
        return StylishReporter(color=config.reporter.color, verbose=config.reporter.verbose)


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
