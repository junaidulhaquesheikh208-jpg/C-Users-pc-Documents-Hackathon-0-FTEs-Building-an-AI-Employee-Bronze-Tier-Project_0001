import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


class OdooIntegration:
    """
    Integration with Odoo Community Edition for accounting
    Uses Odoo's JSON-RPC API for communication
    """
    
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Authenticate and get user ID
        self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Odoo and get user ID
        """
        try:
            url = f"{self.url}/jsonrpc"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, self.username, self.password, {}]
                },
                "id": int(datetime.now().timestamp())
            }
            
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            result = response.json()
            
            if 'result' in result and result['result']:
                self.uid = result['result']
                self.logger.info("Successfully authenticated with Odoo")
                return True
            else:
                self.logger.error(f"Authentication failed: {result}")
                return False
        except Exception as e:
            self.logger.error(f"Error authenticating with Odoo: {e}")
            return False
    
    def _make_request(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Dict:
        """
        Make a generic request to Odoo's JSON-RPC API
        """
        if not self.uid:
            if not self.authenticate():
                return {"error": "Authentication failed"}
        
        try:
            url = f"{self.url}/jsonrpc"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": method,
                    "args": [self.db, self.uid, self.password, model] + (args or []) + ([kwargs] if kwargs else [])
                },
                "id": int(datetime.now().timestamp())
            }
            
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            result = response.json()
            
            if 'result' in result:
                return result['result']
            else:
                self.logger.error(f"Request failed: {result}")
                return {"error": result}
        except Exception as e:
            self.logger.error(f"Error making request to Odoo: {e}")
            return {"error": str(e)}
    
    def create_invoice(self, partner_id: int, lines: List[Dict], date: str = None) -> Dict:
        """
        Create a customer invoice in Odoo
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Prepare invoice values
        vals = {
            'partner_id': partner_id,
            'move_type': 'out_invoice',  # Customer invoice
            'invoice_date': date,
            'invoice_line_ids': [(0, 0, line) for line in lines]  # Create lines
        }
        
        return self._make_request('account.move', 'create', [vals])
    
    def search_invoices(self, domain: List = None) -> List[int]:
        """
        Search for invoices based on domain criteria
        """
        if domain is None:
            domain = []
        
        return self._make_request('account.move', 'search', [domain])
    
    def get_invoice(self, invoice_id: int) -> Dict:
        """
        Get details of a specific invoice
        """
        ids = [invoice_id]
        fields = ['name', 'partner_id', 'amount_total', 'state', 'invoice_date', 'invoice_line_ids']
        
        result = self._make_request('account.move', 'read', [ids, fields])
        
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return {}
    
    def create_partner(self, name: str, email: str = None, phone: str = None) -> Dict:
        """
        Create a new partner (customer/vendor) in Odoo
        """
        vals = {
            'name': name,
            'email': email,
            'phone': phone,
            'is_company': False,  # Default to individual
            'customer_rank': 1,   # Mark as customer
        }
        
        return self._make_request('res.partner', 'create', [vals])
    
    def search_partners(self, domain: List = None) -> List[int]:
        """
        Search for partners based on domain criteria
        """
        if domain is None:
            domain = []
        
        return self._make_request('res.partner', 'search', [domain])
    
    def get_partner(self, partner_id: int) -> Dict:
        """
        Get details of a specific partner
        """
        ids = [partner_id]
        fields = ['name', 'email', 'phone', 'street', 'city', 'country_id']
        
        result = self._make_request('res.partner', 'read', [ids, fields])
        
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return {}
    
    def create_expense(self, partner_id: int, product_id: int, amount: float, date: str = None) -> Dict:
        """
        Create an expense entry in Odoo
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        vals = {
            'partner_id': partner_id,
            'product_id': product_id,
            'date': date,
            'amount_total': amount,
            'state': 'draft'  # Will require approval
        }
        
        return self._make_request('hr.expense', 'create', [vals])
    
    def get_account_balance(self, account_id: int) -> float:
        """
        Get the current balance of an account
        """
        # This is a simplified implementation - actual implementation would depend on Odoo version
        # and specific accounting needs
        return 0.0


# MCP Server Interface for Odoo
class OdooMCPServer:
    def __init__(self, config_path: str = "./odoo_config.json"):
        self.config = self.load_config(config_path)
        self.odoo = None
        if self.config:
            self.odoo = OdooIntegration(
                url=self.config.get("url", ""),
                db=self.config.get("db", ""),
                username=self.config.get("username", ""),
                password=self.config.get("password", "")
            )
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_config(self, config_path: str) -> Dict:
        """Load Odoo API configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Odoo config file not found: {config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading Odoo config: {e}")
            return {}

    def handle_command(self, command: Dict) -> Dict:
        """
        Handle commands from Claude Code via MCP
        Expected commands: create_invoice, search_invoices, create_partner, etc.
        """
        if not self.odoo:
            return {"error": "Odoo integration not configured or authentication failed"}
        
        cmd_type = command.get("type")
        
        if cmd_type == "create_invoice":
            partner_id = command.get("partner_id")
            lines = command.get("lines", [])
            date = command.get("date")
            return self.odoo.create_invoice(partner_id, lines, date)
        
        elif cmd_type == "search_invoices":
            domain = command.get("domain", [])
            return self.odoo.search_invoices(domain)
        
        elif cmd_type == "get_invoice":
            invoice_id = command.get("invoice_id")
            return self.odoo.get_invoice(invoice_id)
        
        elif cmd_type == "create_partner":
            name = command.get("name")
            email = command.get("email")
            phone = command.get("phone")
            return self.odoo.create_partner(name, email, phone)
        
        elif cmd_type == "search_partners":
            domain = command.get("domain", [])
            return self.odoo.search_partners(domain)
        
        elif cmd_type == "get_partner":
            partner_id = command.get("partner_id")
            return self.odoo.get_partner(partner_id)
        
        elif cmd_type == "create_expense":
            partner_id = command.get("partner_id")
            product_id = command.get("product_id")
            amount = command.get("amount")
            date = command.get("date")
            return self.odoo.create_expense(partner_id, product_id, amount, date)
        
        else:
            return {"error": f"Unknown command type: {cmd_type}"}


# Example usage
if __name__ == "__main__":
    # This would normally be run as an MCP server
    # odoo_server = OdooMCPServer()
    print("Odoo MCP Server initialized")