# audit_logic.py
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any


SUBSCRIPTION_PATTERNS = {
    'netflix.com': 'Netflix',
    'spotify.com': 'Spotify',
    'adobe.com': 'Adobe Creative Cloud',
    'notion.so': 'Notion',
    'slack.com': 'Slack',
    'zoom.us': 'Zoom',
    'microsoft.com': 'Microsoft 365',
    'google.com': 'Google Workspace',
    'aws.amazon.com': 'Amazon Web Services',
    'heroku.com': 'Heroku',
    'digitalocean.com': 'DigitalOcean',
    'stripe.com': 'Stripe Fees',
    'paypal.com': 'PayPal Processing',
    'square.com': 'Square Processing',
}


def analyze_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a transaction to determine its type and category
    """
    description = transaction.get('description', '').lower()
    amount = transaction.get('amount', 0)
    date = transaction.get('date', '')
    
    # Check for subscription patterns
    for pattern, name in SUBSCRIPTION_PATTERNS.items():
        if pattern in description:
            return {
                'type': 'subscription',
                'name': name,
                'amount': amount,
                'date': date,
                'category': 'Software/Service'
            }
    
    # Check for other common transaction types
    if any(word in description for word in ['payment', 'transfer', 'deposit']):
        return {
            'type': 'payment',
            'name': description.title(),
            'amount': amount,
            'date': date,
            'category': 'Payment'
        }
    
    if any(word in description for word in ['purchase', 'buy', 'order', 'amazon', 'store']):
        return {
            'type': 'purchase',
            'name': description.title(),
            'amount': amount,
            'date': date,
            'category': 'Purchase'
        }
    
    # Default transaction type
    return {
        'type': 'unknown',
        'name': description.title(),
        'amount': amount,
        'date': date,
        'category': 'Uncategorized'
    }


def analyze_weekly_transactions(transactions: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Analyze transactions for a specific week period
    """
    # Filter transactions for the week
    weekly_transactions = []
    for transaction in transactions:
        trans_date_str = transaction.get('date', '')
        try:
            trans_date = datetime.strptime(trans_date_str, '%Y-%m-%d')
            if start_date <= trans_date <= end_date:
                weekly_transactions.append(transaction)
        except ValueError:
            # Skip invalid dates
            continue
    
    # Categorize transactions
    categorized = {'subscriptions': [], 'payments': [], 'purchases': [], 'other': []}
    total_spent = 0
    total_income = 0
    
    for transaction in weekly_transactions:
        analyzed = analyze_transaction(transaction)
        trans_type = analyzed['type']
        amount = analyzed['amount']
        
        if amount < 0:
            total_spent += abs(amount)
        else:
            total_income += amount
        
        if trans_type == 'subscription':
            categorized['subscriptions'].append(analyzed)
        elif trans_type == 'payment':
            categorized['payments'].append(analyzed)
        elif trans_type == 'purchase':
            categorized['purchases'].append(analyzed)
        else:
            categorized['other'].append(analyzed)
    
    # Identify potential issues
    issues = []
    for sub in categorized['subscriptions']:
        if sub['amount'] > 100:  # Flag expensive subscriptions
            issues.append(f"Expensive subscription: {sub['name']} (${sub['amount']})")
    
    # Find duplicate transactions
    seen_transactions = set()
    duplicates = []
    for trans in weekly_transactions:
        desc_amount = (trans.get('description', ''), trans.get('amount', 0))
        if desc_amount in seen_transactions:
            duplicates.append(trans)
        else:
            seen_transactions.add(desc_amount)
    
    if duplicates:
        issues.append(f"Potential duplicate transactions: {len(duplicates)} found")
    
    return {
        'total_income': total_income,
        'total_spent': total_spent,
        'net_change': total_income - total_spent,
        'transactions': categorized,
        'issues': issues,
        'transaction_count': len(weekly_transactions)
    }


def generate_ceo_briefing_data(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Generate data for the CEO briefing based on weekly analysis
    """
    # This would normally pull from actual transaction data
    # For now, we'll simulate with sample data
    sample_transactions = [
        {'description': 'Netflix.com Subscription', 'amount': -15.99, 'date': start_date.strftime('%Y-%m-%d')},
        {'description': 'Adobe Creative Cloud', 'amount': -52.99, 'date': start_date.strftime('%Y-%m-%d')},
        {'description': 'Client Payment - Project Alpha', 'amount': 2500.00, 'date': start_date.strftime('%Y-%m-%d')},
        {'description': 'AWS Services', 'amount': -89.50, 'date': (start_date + timedelta(days=2)).strftime('%Y-%m-%d')},
        {'description': 'Office Supplies', 'amount': -45.20, 'date': (start_date + timedelta(days=3)).strftime('%Y-%m-%d')},
        {'description': 'Client Payment - Project Beta', 'amount': 1800.00, 'date': (start_date + timedelta(days=4)).strftime('%Y-%m-%d')},
    ]
    
    analysis = analyze_weekly_transactions(sample_transactions, start_date, end_date)
    
    # Generate proactive suggestions
    suggestions = []
    
    # Check for unused subscriptions
    active_subs = analysis['transactions']['subscriptions']
    if active_subs:
        sub_names = [sub['name'] for sub in active_subs]
        suggestions.append(f"Review subscriptions: {', '.join(sub_names)}. Are they all necessary?")
    
    # Check for high spending categories
    if analysis['total_spent'] > 500:
        suggestions.append("High spending this week. Consider reviewing expenses.")
    
    # Add any issues found
    suggestions.extend(analysis['issues'])
    
    return {
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'revenue': {
            'weekly': analysis['total_income'],
            'spent': analysis['total_spent'],
            'net': analysis['net_change']
        },
        'transactions': analysis['transactions'],
        'issues': analysis['issues'],
        'suggestions': suggestions,
        'summary_stats': {
            'transaction_count': analysis['transaction_count'],
            'subscription_count': len(active_subs)
        }
    }


def format_briefing_markdown(briefing_data: Dict[str, Any]) -> str:
    """
    Format the briefing data as Markdown for the Obsidian vault
    """
    start_date = briefing_data['period_start']
    end_date = briefing_data['period_end']
    revenue = briefing_data['revenue']
    suggestions = briefing_data['suggestions']
    
    markdown = f"""# Monday Morning CEO Briefing - {datetime.now().strftime('%Y-%m-%d')}

---
generated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
period: {start_date} to {end_date}
---

## Executive Summary
Weekly summary of business activities and achievements.

## Revenue
- **This Week**: ${revenue['weekly']:.2f}
- **Spent**: ${revenue['spent']:.2f}
- **Net**: ${revenue['net']:.2f}
- **Trend**: {"Positive" if revenue['net'] > 0 else "Negative"}

## Transaction Summary
- **Total Transactions**: {briefing_data['summary_stats']['transaction_count']}
- **Active Subscriptions**: {briefing_data['summary_stats']['subscription_count']}

## Completed Tasks
- Weekly financial audit completed
- Transaction categorization performed
- Issue identification completed

## Bottlenecks
- {"None identified" if not briefing_data['issues'] else '; '.join(briefing_data['issues'])}

## Proactive Suggestions

### Cost Optimization
"""
    
    if suggestions:
        for suggestion in suggestions:
            markdown += f"- {suggestion}\n"
    else:
        markdown += "- No specific suggestions at this time\n"
    
    markdown += """

### Upcoming Actions
- Review flagged transactions
- Assess subscription values
- Plan next week's budget

---
*Generated by AI Employee v0.1*
"""
    
    return markdown


# Example usage
if __name__ == "__main__":
    # Example of how this would be used in the orchestrator
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    
    briefing_data = generate_ceo_briefing_data(start_of_week, end_of_week)
    briefing_markdown = format_briefing_markdown(briefing_data)
    
    print("Sample CEO Briefing:")
    print(briefing_markdown)