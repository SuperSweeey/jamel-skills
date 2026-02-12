#!/usr/bin/env python3
"""
Cubox API Configuration Manager
Securely stores and retrieves encrypted API URL
"""

import sys
import json
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet


class ConfigManager:
    """Manage encrypted Cubox API configuration"""
    
    def __init__(self):
        # Config file location in skill directory
        self.skill_dir = Path(__file__).parent.parent
        self.config_file = self.skill_dir / "config" / "cubox_config.enc"
        self.key_file = self.skill_dir / "config" / ".key"
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(exist_ok=True)
    
    def _get_or_create_key(self):
        """Get existing encryption key or create a new one"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate a new key based on machine-specific info
            # This makes the config only work on this machine
            import platform
            import uuid
            
            # Combine machine-specific identifiers
            machine_id = f"{platform.node()}-{uuid.getnode()}"
            
            # Create a deterministic key from machine ID
            key_material = hashlib.sha256(machine_id.encode()).digest()
            key = base64.urlsafe_b64encode(key_material)
            
            # Save the key
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Make key file hidden on Windows
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.key_file), 2)
            except:
                pass
            
            return key
    
    def save_api_url(self, api_url):
        """
        Save API URL with encryption
        
        Args:
            api_url: The Cubox API URL to save
        
        Returns:
            (success: bool, message: str)
        """
        try:
            # Get encryption key
            key = self._get_or_create_key()
            cipher = Fernet(key)
            
            # Prepare config data
            config_data = {
                "api_url": api_url,
                "version": "1.0"
            }
            
            # Encrypt the data
            json_data = json.dumps(config_data).encode()
            encrypted_data = cipher.encrypt(json_data)
            
            # Save to file
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            return True, f"✅ API URL 已加密保存到:\n{self.config_file}"
        
        except Exception as e:
            return False, f"❌ 保存失败: {str(e)}"
    
    def load_api_url(self):
        """
        Load and decrypt API URL
        
        Returns:
            (api_url: str or None, message: str)
        """
        try:
            # Check if config exists
            if not self.config_file.exists():
                return None, "配置文件不存在，需要首次设置 API URL"
            
            # Get encryption key
            key = self._get_or_create_key()
            cipher = Fernet(key)
            
            # Read and decrypt
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher.decrypt(encrypted_data)
            config_data = json.loads(decrypted_data.decode())
            
            api_url = config_data.get("api_url")
            
            if api_url:
                return api_url, "✅ 成功加载 API URL"
            else:
                return None, "配置文件损坏"
        
        except Exception as e:
            return None, f"❌ 加载失败: {str(e)}"
    
    def config_exists(self):
        """Check if config file exists"""
        return self.config_file.exists()
    
    def delete_config(self):
        """Delete saved configuration"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            if self.key_file.exists():
                self.key_file.unlink()
            return True, "✅ 配置已删除"
        except Exception as e:
            return False, f"❌ 删除失败: {str(e)}"


def main():
    """Command-line interface for config management"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Cubox API Configuration Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save API URL (first time or update)
  python config_manager.py --save --api-url "https://cubox.pro/c/api/..."
  
  # Load API URL (check current config)
  python config_manager.py --load
  
  # Delete saved config
  python config_manager.py --delete
        """
    )
    
    parser.add_argument('--save', action='store_true',
                        help='Save API URL')
    parser.add_argument('--load', action='store_true',
                        help='Load and display API URL')
    parser.add_argument('--delete', action='store_true',
                        help='Delete saved configuration')
    parser.add_argument('--api-url',
                        help='API URL to save (required with --save)')
    parser.add_argument('--check', action='store_true',
                        help='Check if config exists')
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    if args.save:
        if not args.api_url:
            print("❌ 错误: --save 需要提供 --api-url 参数")
            sys.exit(1)
        
        success, message = manager.save_api_url(args.api_url)
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.load:
        api_url, message = manager.load_api_url()
        print(message)
        if api_url:
            print(f"API URL: {api_url[:50]}...")
        sys.exit(0 if api_url else 1)
    
    elif args.delete:
        success, message = manager.delete_config()
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.check:
        if manager.config_exists():
            print("✅ 配置文件存在")
            sys.exit(0)
        else:
            print("❌ 配置文件不存在")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
