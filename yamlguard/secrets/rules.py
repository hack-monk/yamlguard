"""
Secrets detection rules and entropy analysis.

Provides comprehensive secrets detection using curated regex patterns,
Shannon entropy analysis, and context-aware heuristics for YAML files.
"""

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union

from pydantic import BaseModel, Field


class SecretMatch(BaseModel):
    """Represents a detected secret with detailed information."""
    
    line: int = Field(..., description="Line number (1-based)")
    column: int = Field(..., description="Column number (1-based)")
    value: str = Field(..., description="Detected secret value")
    rule: str = Field(..., description="Rule that detected the secret")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    context: str = Field(..., description="Context around the secret")
    path: str = Field(..., description="YAML path to the secret")
    severity: str = Field(default="error", description="Severity level")


class SecretRule(BaseModel):
    """Represents a secret detection rule."""
    
    name: str = Field(..., description="Rule name")
    pattern: str = Field(..., description="Regex pattern")
    description: str = Field(..., description="Rule description")
    confidence: float = Field(default=0.8, description="Base confidence score")
    context_keys: List[str] = Field(default_factory=list, description="Context keys that increase confidence")
    entropy_threshold: float = Field(default=4.0, description="Minimum entropy threshold")


class SecretsRuleEngine:
    """
    Engine for detecting secrets in YAML content.
    
    Uses curated regex patterns, entropy analysis, and context-aware
    heuristics to detect various types of secrets and credentials.
    """
    
    def __init__(self, entropy_threshold: float = 4.5):
        """
        Initialize the secrets rule engine.
        
        Args:
            entropy_threshold: Minimum entropy threshold for detection
        """
        self.entropy_threshold = entropy_threshold
        self.rules = self._initialize_rules()
        self.compiled_patterns: Dict[str, Pattern] = {}
        self._compile_patterns()
    
    def _initialize_rules(self) -> List[SecretRule]:
        """Initialize built-in secret detection rules."""
        return [
            # AWS
            SecretRule(
                name="aws-access-key",
                pattern=r"AKIA[0-9A-Z]{16}",
                description="AWS Access Key ID",
                confidence=0.9,
                context_keys=["aws", "access", "key", "secret"]
            ),
            SecretRule(
                name="aws-secret-key",
                pattern=r"[A-Za-z0-9/+=]{40}",
                description="AWS Secret Access Key",
                confidence=0.8,
                context_keys=["aws", "secret", "access", "key"]
            ),
            
            # GitHub
            SecretRule(
                name="github-token",
                pattern=r"ghp_[A-Za-z0-9]{36}",
                description="GitHub Personal Access Token",
                confidence=0.9,
                context_keys=["github", "token", "auth"]
            ),
            SecretRule(
                name="github-app-token",
                pattern=r"ghs_[A-Za-z0-9]{36}",
                description="GitHub App Token",
                confidence=0.9,
                context_keys=["github", "app", "token"]
            ),
            
            # GitLab
            SecretRule(
                name="gitlab-token",
                pattern=r"glpat-[A-Za-z0-9_-]{20}",
                description="GitLab Personal Access Token",
                confidence=0.9,
                context_keys=["gitlab", "token", "auth"]
            ),
            
            # Slack
            SecretRule(
                name="slack-token",
                pattern=r"xox[baprs]-[A-Za-z0-9-]+",
                description="Slack Bot/App Token",
                confidence=0.8,
                context_keys=["slack", "token", "bot", "app"]
            ),
            
            # Twilio
            SecretRule(
                name="twilio-sid",
                pattern=r"AC[a-f0-9]{32}",
                description="Twilio Account SID",
                confidence=0.8,
                context_keys=["twilio", "sid", "account"]
            ),
            SecretRule(
                name="twilio-auth-token",
                pattern=r"[a-f0-9]{32}",
                description="Twilio Auth Token",
                confidence=0.7,
                context_keys=["twilio", "auth", "token"]
            ),
            
            # Database URIs
            SecretRule(
                name="database-uri",
                pattern=r"(?:mysql|postgresql|mongodb|redis)://[^:\s]+:[^@\s]+@[^/\s]+",
                description="Database URI with credentials",
                confidence=0.9,
                context_keys=["database", "uri", "connection", "url"]
            ),
            
            # Private Keys
            SecretRule(
                name="private-key",
                pattern=r"-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----",
                description="Private Key",
                confidence=0.9,
                context_keys=["private", "key", "pem", "cert"]
            ),
            SecretRule(
                name="ssh-private-key",
                pattern=r"-----BEGIN OPENSSH PRIVATE KEY-----",
                description="SSH Private Key",
                confidence=0.9,
                context_keys=["ssh", "private", "key"]
            ),
            
            # API Keys (generic)
            SecretRule(
                name="api-key",
                pattern=r"[A-Za-z0-9]{32,}",
                description="Generic API Key",
                confidence=0.6,
                context_keys=["api", "key", "token", "auth"],
                entropy_threshold=4.5
            ),
            
            # JWT Tokens
            SecretRule(
                name="jwt-token",
                pattern=r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                description="JWT Token",
                confidence=0.8,
                context_keys=["jwt", "token", "bearer", "auth"]
            ),
            
            # Docker Registry
            SecretRule(
                name="docker-registry",
                pattern=r"[a-zA-Z0-9-]+\.azurecr\.io",
                description="Docker Registry URL",
                confidence=0.7,
                context_keys=["docker", "registry", "image", "container"]
            ),
        ]
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        for rule in self.rules:
            try:
                self.compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
            except re.error as e:
                print(f"Warning: Invalid regex pattern for rule {rule.name}: {e}")
    
    def scan_file(self, file_path: Union[str, Path]) -> List[SecretMatch]:
        """
        Scan a file for secrets.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of detected secrets
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return self.scan_content(content, str(file_path))
    
    def scan_content(self, content: str, source: str = "<string>") -> List[SecretMatch]:
        """
        Scan content for secrets.
        
        Args:
            content: Content to scan
            source: Source identifier for error reporting
            
        Returns:
            List of detected secrets
        """
        matches = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Check each rule
            for rule in self.rules:
                pattern = self.compiled_patterns.get(rule.name)
                if not pattern:
                    continue
                
                for match in pattern.finditer(line):
                    # Calculate confidence based on context
                    confidence = self._calculate_confidence(
                        rule, match.group(), line, line_num, lines
                    )
                    
                    # Skip low-confidence matches
                    if confidence < 0.5:
                        continue
                    
                    # Get context around the match
                    context = self._get_context(lines, line_num, match.start(), match.end())
                    
                    # Determine YAML path
                    yaml_path = self._get_yaml_path(content, line_num)
                    
                    secret_match = SecretMatch(
                        line=line_num,
                        column=match.start() + 1,
                        value=match.group(),
                        rule=rule.name,
                        confidence=confidence,
                        context=context,
                        path=yaml_path,
                        severity="error" if confidence > 0.8 else "warning"
                    )
                    
                    matches.append(secret_match)
        
        return matches
    
    def _calculate_confidence(self, rule: SecretRule, value: str, line: str, 
                             line_num: int, all_lines: List[str]) -> float:
        """
        Calculate confidence score for a potential secret.
        
        Args:
            rule: The rule that matched
            value: The matched value
            line: The line containing the match
            line_num: Line number
            all_lines: All lines in the content
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = rule.confidence
        
        # Check entropy if threshold is set
        if rule.entropy_threshold > 0:
            entropy = self._calculate_entropy(value)
            if entropy < rule.entropy_threshold:
                confidence *= 0.5  # Reduce confidence for low entropy
        
        # Check context keywords
        line_lower = line.lower()
        context_matches = sum(1 for key in rule.context_keys if key in line_lower)
        if context_matches > 0:
            confidence += 0.1 * context_matches
        
        # Check for common false positives
        false_positive_patterns = [
            r'example\.com',
            r'localhost',
            r'127\.0\.0\.1',
            r'placeholder',
            r'test',
            r'dummy',
            r'sample',
        ]
        
        for pattern in false_positive_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                confidence *= 0.3  # Reduce confidence for likely false positives
        
        # Check for allowlist patterns
        allowlist_patterns = [
            r'# yamlguard:allow',
            r'# yamlguard:ignore',
        ]
        
        for pattern in allowlist_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return 0.0  # Explicitly allowed
        
        return min(confidence, 1.0)
    
    def _calculate_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy of a string.
        
        Args:
            text: Text to analyze
            
        Returns:
            Entropy value
        """
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _get_context(self, lines: List[str], line_num: int, start: int, end: int) -> str:
        """
        Get context around a match.
        
        Args:
            lines: All lines
            line_num: Line number of the match
            start: Start position of the match
            end: End position of the match
            
        Returns:
            Context string
        """
        context_lines = []
        
        # Get surrounding lines
        start_line = max(0, line_num - 2)
        end_line = min(len(lines), line_num + 1)
        
        for i in range(start_line, end_line):
            if i < len(lines):
                prefix = ">>> " if i == line_num - 1 else "    "
                context_lines.append(f"{prefix}{lines[i]}")
        
        return "\n".join(context_lines)
    
    def _get_yaml_path(self, content: str, line_num: int) -> str:
        """
        Get YAML path for a line number.
        
        Args:
            content: YAML content
            line_num: Line number
            
        Returns:
            YAML path string
        """
        # This is a simplified implementation
        # In practice, you'd parse the YAML structure to get the exact path
        lines = content.splitlines()
        if line_num <= len(lines):
            line = lines[line_num - 1]
            if ':' in line:
                key = line.split(':')[0].strip()
                return f"root.{key}"
        
        return "root"
    
    def add_custom_rule(self, rule: SecretRule) -> None:
        """
        Add a custom secret detection rule.
        
        Args:
            rule: Custom rule to add
        """
        self.rules.append(rule)
        try:
            self.compiled_patterns[rule.name] = re.compile(rule.pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def get_rule_info(self) -> List[Dict[str, Any]]:
        """Get information about all rules."""
        return [
            {
                'name': rule.name,
                'description': rule.description,
                'confidence': rule.confidence,
                'entropy_threshold': rule.entropy_threshold,
                'context_keys': rule.context_keys
            }
            for rule in self.rules
        ]
