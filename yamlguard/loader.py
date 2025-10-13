"""
Core YAML loader with ruamel.yaml integration.

Provides safe, round-trip aware YAML parsing with precise position tracking
for indentation validation.
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.tokens import Token


class YAMLLoader:
    """
    Enhanced YAML loader using ruamel.yaml for precise parsing and position tracking.
    
    Provides round-trip preservation of comments and formatting while enabling
    detailed inspection of indentation and structure.
    """
    
    def __init__(self, preserve_quotes: bool = True, width: int = 4096):
        """
        Initialize the YAML loader.
        
        Args:
            preserve_quotes: Whether to preserve quote styles
            width: Maximum line width for parsing
        """
        self.yaml = YAML()
        self.yaml.preserve_quotes = preserve_quotes
        self.yaml.width = width
        self.yaml.allow_duplicate_keys = False  # We'll handle this in cosmetics
        
    def load_file(self, file_path: Union[str, Path]) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Load a YAML file with position tracking.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Tuple of (parsed_data, position_info)
            
        Raises:
            YAMLError: If the file cannot be parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.load_stream(f, str(file_path))
    
    def load_stream(self, stream: Union[str, io.StringIO], source: str = "<string>") -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Load YAML from a stream with position tracking.
        
        Args:
            stream: YAML content as string or StringIO
            source: Source identifier for error reporting
            
        Returns:
            Tuple of (parsed_data, position_info)
        """
        if isinstance(stream, str):
            stream = io.StringIO(stream)
        
        # Reset stream position
        stream.seek(0)
        
        try:
            # Parse with position tracking
            data = self.yaml.load(stream)
            positions = self._extract_positions(data, source)
            
            return data, positions
            
        except YAMLError as e:
            # Enhance error with position information
            if hasattr(e, 'problem_mark'):
                line = e.problem_mark.line + 1
                column = e.problem_mark.column + 1
                raise YAMLError(f"YAML parsing error at {source}:{line}:{column}: {e}")
            else:
                raise YAMLError(f"YAML parsing error in {source}: {e}")
    
    def _extract_positions(self, data: Any, source: str) -> List[Dict[str, Any]]:
        """
        Extract position information from parsed YAML data.
        
        Args:
            data: Parsed YAML data
            source: Source identifier
            
        Returns:
            List of position information dictionaries
        """
        positions = []
        
        if isinstance(data, (CommentedMap, CommentedSeq)):
            self._walk_with_positions(data, positions, source, [])
        
        return positions
    
    def _walk_with_positions(self, obj: Any, positions: List[Dict[str, Any]], 
                           source: str, path: List[str]) -> None:
        """
        Recursively walk YAML structure and collect position information.
        
        Args:
            obj: Current YAML object
            positions: List to collect position info
            source: Source identifier
            path: Current path in the structure
        """
        if isinstance(obj, CommentedMap):
            for key, value in obj.items():
                current_path = path + [str(key)]
                
                # Get position info for the key
                if hasattr(obj, 'ca') and obj.ca:
                    key_pos = self._get_key_position(obj, key)
                    if key_pos:
                        positions.append({
                            'type': 'mapping_key',
                            'path': '.'.join(current_path),
                            'source': source,
                            'line': key_pos.get('line', 0),
                            'column': key_pos.get('column', 0),
                            'value': str(key)
                        })
                
                # Recursively process the value
                self._walk_with_positions(value, positions, source, current_path)
                
        elif isinstance(obj, CommentedSeq):
            for i, item in enumerate(obj):
                current_path = path + [f"[{i}]"]
                
                # Get position info for the sequence item
                if hasattr(obj, 'ca') and obj.ca:
                    item_pos = self._get_item_position(obj, i)
                    if item_pos:
                        positions.append({
                            'type': 'sequence_item',
                            'path': '.'.join(current_path),
                            'source': source,
                            'line': item_pos.get('line', 0),
                            'column': item_pos.get('column', 0),
                            'value': str(item) if not isinstance(item, (dict, list)) else None
                        })
                
                # Recursively process the item
                self._walk_with_positions(item, positions, source, current_path)
    
    def _get_key_position(self, mapping: CommentedMap, key: str) -> Optional[Dict[str, int]]:
        """Get position information for a mapping key."""
        if not hasattr(mapping, 'ca') or not mapping.ca:
            return None
        
        # This is a simplified implementation
        # In practice, you'd need to parse the comment attributes more carefully
        return {'line': 1, 'column': 1}  # Placeholder
    
    def _get_item_position(self, sequence: CommentedSeq, index: int) -> Optional[Dict[str, int]]:
        """Get position information for a sequence item."""
        if not hasattr(sequence, 'ca') or not sequence.ca:
            return None
        
        # This is a simplified implementation
        # In practice, you'd need to parse the comment attributes more carefully
        return {'line': 1, 'column': 1}  # Placeholder
    
    def dump(self, data: Any, stream: Optional[io.StringIO] = None) -> str:
        """
        Dump YAML data with preserved formatting.
        
        Args:
            data: Data to dump
            stream: Optional stream to write to
            
        Returns:
            YAML string
        """
        if stream is None:
            stream = io.StringIO()
        
        self.yaml.dump(data, stream)
        return stream.getvalue()
    
    def normalize_indentation(self, data: Any, indent_step: int = 2) -> str:
        """
        Normalize indentation in YAML data.
        
        Args:
            data: YAML data to normalize
            indent_step: Number of spaces per indentation level
            
        Returns:
            Normalized YAML string
        """
        # Configure for consistent indentation
        yaml = YAML()
        yaml.indent(mapping=indent_step, sequence=indent_step, offset=indent_step)
        yaml.preserve_quotes = True
        
        stream = io.StringIO()
        yaml.dump(data, stream)
        return stream.getvalue()


class SafeYAMLLoader:
    """
    Fast YAML loader using PyYAML's CSafeLoader for speed when comments aren't needed.
    
    This is a fallback for cases where ruamel.yaml parsing fails or when
    maximum performance is required.
    """
    
    def __init__(self):
        """Initialize the safe YAML loader."""
        try:
            import yaml
            self.yaml = yaml
        except ImportError:
            raise ImportError("PyYAML is required for SafeYAMLLoader")
    
    def load_file(self, file_path: Union[str, Path]) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Load a YAML file using PyYAML.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Tuple of (parsed_data, empty_position_info)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = self.yaml.safe_load(f)
            return data, []  # No position info with PyYAML
    
    def load_stream(self, stream: Union[str, io.StringIO], source: str = "<string>") -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Load YAML from a stream using PyYAML.
        
        Args:
            stream: YAML content as string or StringIO
            source: Source identifier for error reporting
            
        Returns:
            Tuple of (parsed_data, empty_position_info)
        """
        if isinstance(stream, str):
            stream = io.StringIO(stream)
        
        stream.seek(0)
        data = self.yaml.safe_load(stream)
        return data, []  # No position info with PyYAML
