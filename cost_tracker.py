#!/usr/bin/env python3
"""
Cost tracking and budget management for Fashn.ai usage
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import matplotlib.pyplot as plt

class CostTracker:
    """Track API costs, generate reports, set budgets"""
    
    def __init__(self, data_file: str = "cost_data.json"):
        self.data_file = Path(data_file)
        self.data = self._load_data()
        
        # Pricing (Fashn.ai)
        self.cost_per_image = 0.04  # $40 per 1000 = $0.04 per image
    
    def _load_data(self) -> Dict:
        """Load cost data from file"""
        if self.data_file.exists():
            with open(self.data_file) as f:
                return json.load(f)
        
        return {
            "total_images": 0,
            "total_cost": 0.0,
            "daily_usage": {},
            "monthly_usage": {},
            "transactions": []
        }
    
    def _save_data(self):
        """Save cost data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def log_generation(self, num_images: int = 1, metadata: Dict = None):
        """Log a photo generation event"""
        
        cost = num_images * self.cost_per_image
        timestamp = datetime.now().isoformat()
        date_key = datetime.now().strftime("%Y-%m-%d")
        month_key = datetime.now().strftime("%Y-%m")
        
        # Update totals
        self.data["total_images"] += num_images
        self.data["total_cost"] += cost
        
        # Update daily
        if date_key not in self.data["daily_usage"]:
            self.data["daily_usage"][date_key] = {"images": 0, "cost": 0.0}
        
        self.data["daily_usage"][date_key]["images"] += num_images
        self.data["daily_usage"][date_key]["cost"] += cost
        
        # Update monthly
        if month_key not in self.data["monthly_usage"]:
            self.data["monthly_usage"][month_key] = {"images": 0, "cost": 0.0}
        
        self.data["monthly_usage"][month_key]["images"] += num_images
        self.data["monthly_usage"][month_key]["cost"] += cost
        
        # Log transaction
        transaction = {
            "timestamp": timestamp,
            "images": num_images,
            "cost": cost,
            "metadata": metadata or {}
        }
        
        self.data["transactions"].append(transaction)
        
        self._save_data()
    
    def get_daily_usage(self, days: int = 7) -> List[Dict]:
        """Get usage for last N days"""
        
        result = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            
            usage = self.data["daily_usage"].get(date_key, {"images": 0, "cost": 0.0})
            
            result.append({
                "date": date_key,
                **usage
            })
        
        return list(reversed(result))
    
    def get_monthly_summary(self) -> Dict:
        """Get current month summary"""
        
        month_key = datetime.now().strftime("%Y-%m")
        
        return self.data["monthly_usage"].get(month_key, {
            "images": 0,
            "cost": 0.0
        })
    
    def check_budget(self, daily_limit: float = None, monthly_limit: float = None) -> Dict:
        """Check if usage exceeds budget limits"""
        
        warnings = []
        
        # Daily check
        if daily_limit:
            today_key = datetime.now().strftime("%Y-%m-%d")
            today_usage = self.data["daily_usage"].get(today_key, {"cost": 0.0})
            
            if today_usage["cost"] >= daily_limit:
                warnings.append({
                    "type": "daily",
                    "limit": daily_limit,
                    "usage": today_usage["cost"],
                    "exceeded": True
                })
        
        # Monthly check
        if monthly_limit:
            month_summary = self.get_monthly_summary()
            
            if month_summary["cost"] >= monthly_limit:
                warnings.append({
                    "type": "monthly",
                    "limit": monthly_limit,
                    "usage": month_summary["cost"],
                    "exceeded": True
                })
        
        return {
            "budget_ok": len(warnings) == 0,
            "warnings": warnings
        }
    
    def generate_report(self, days: int = 7):
        """Generate formatted cost report"""
        
        print("\n" + "="*70)
        print("💰 COST TRACKER REPORT")
        print("="*70)
        
        # Overall stats
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Images:      {self.data['total_images']:,}")
        print(f"   Total Cost:        ${self.data['total_cost']:.2f}")
        print(f"   Avg Cost/Image:    ${self.cost_per_image:.4f}")
        
        # Monthly summary
        month_summary = self.get_monthly_summary()
        month_name = datetime.now().strftime("%B %Y")
        print(f"\n📅 {month_name}:")
        print(f"   Images:            {month_summary['images']:,}")
        print(f"   Cost:              ${month_summary['cost']:.2f}")
        
        # Daily breakdown
        daily_usage = self.get_daily_usage(days)
        print(f"\n📆 Last {days} Days:")
        print(f"   {'Date':<12} {'Images':<10} {'Cost':<10}")
        print(f"   {'-'*12} {'-'*10} {'-'*10}")
        
        for day in daily_usage:
            print(f"   {day['date']:<12} {day['images']:<10} ${day['cost']:<9.2f}")
        
        # Recent transactions
        recent_txns = self.data["transactions"][-10:]
        
        if recent_txns:
            print(f"\n📝 Recent Transactions:")
            for txn in reversed(recent_txns):
                time = datetime.fromisoformat(txn['timestamp']).strftime("%Y-%m-%d %H:%M")
                print(f"   {time} | {txn['images']} images | ${txn['cost']:.2f}")
        
        print("="*70 + "\n")
    
    def plot_usage(self, days: int = 30, save_path: str = "cost_chart.png"):
        """Generate usage chart"""
        
        daily_usage = self.get_daily_usage(days)
        
        dates = [d['date'] for d in daily_usage]
        images = [d['images'] for d in daily_usage]
        costs = [d['cost'] for d in daily_usage]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Images per day
        ax1.bar(dates, images, color='skyblue')
        ax1.set_title(f'Images Generated - Last {days} Days')
        ax1.set_ylabel('Images')
        ax1.grid(axis='y', alpha=0.3)
        
        # Cost per day
        ax2.bar(dates, costs, color='lightcoral')
        ax2.set_title('Daily Cost')
        ax2.set_ylabel('Cost ($)')
        ax2.set_xlabel('Date')
        ax2.grid(axis='y', alpha=0.3)
        
        # Rotate x labels
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        plt.close()
        
        print(f"📊 Chart saved: {save_path}")


# CLI usage
if __name__ == "__main__":
    import sys
    
    tracker = CostTracker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "report":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            tracker.generate_report(days)
        
        elif command == "log":
            num_images = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            tracker.log_generation(num_images)
            print(f"✅ Logged {num_images} image(s)")
        
        elif command == "budget":
            daily = float(sys.argv[2]) if len(sys.argv) > 2 else None
            monthly = float(sys.argv[3]) if len(sys.argv) > 3 else None
            
            result = tracker.check_budget(daily, monthly)
            
            if result["budget_ok"]:
                print("✅ Within budget")
            else:
                print("⚠️  BUDGET EXCEEDED!")
                for warning in result["warnings"]:
                    print(f"   {warning['type'].title()}: ${warning['usage']:.2f} / ${warning['limit']:.2f}")
        
        elif command == "plot":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            output = sys.argv[3] if len(sys.argv) > 3 else "cost_chart.png"
            tracker.plot_usage(days, output)
        
        else:
            print("Usage: python cost_tracker.py [report|log|budget|plot]")
    
    else:
        # Default: show report
        tracker.generate_report()
