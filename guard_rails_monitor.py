#!/usr/bin/env python3
"""
MediaHub Guard Rails Monitor
Automated continuous monitoring of implementation status and feature compliance
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# Add server path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.routes.enhanced.implementation_guard_rails import ImplementationGuardRails

class GuardRailsMonitor:
    """Continuous monitoring system for MediaHub implementation compliance"""
    
    def __init__(self, app_root: str, config_file: str = None):
        self.app_root = Path(app_root)
        self.config_file = config_file or str(self.app_root / 'guard_rails_config.json')
        self.guard_rails = ImplementationGuardRails(str(self.app_root))
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.app_root / 'guard_rails.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize monitoring state
        self.last_audit_results = None
        self.deployment_blocked = False
        self.violation_count = 0
        
    def _load_config(self) -> Dict[str, Any]:
        """Load guard rails configuration"""
        default_config = {
            "monitoring": {
                "enabled": True,
                "interval_seconds": 300,  # 5 minutes
                "auto_block_deployment": True,
                "max_violations_before_block": 3
            },
            "thresholds": {
                "minimum_pillar_score": 90,
                "minimum_category_score": 85,
                "minimum_overall_score": 88,
                "critical_features": [
                    "omnibox_search",
                    "hero_interface", 
                    "profile_system",
                    "api_integrations"
                ]
            },
            "notifications": {
                "enabled": True,
                "email_alerts": False,
                "webhook_url": None,
                "slack_webhook": None
            },
            "deployment_gates": {
                "require_all_pillars_pass": True,
                "require_all_categories_pass": False,
                "allow_warnings": True,
                "block_on_critical_violations": True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                self.logger.info(f"Created default config file: {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            
        return default_config
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        self.logger.info("Starting MediaHub Guard Rails continuous monitoring")
        
        if not self.config["monitoring"]["enabled"]:
            self.logger.info("Monitoring is disabled in configuration")
            return
        
        interval = self.config["monitoring"]["interval_seconds"]
        
        try:
            while True:
                self.logger.info("Running scheduled audit check...")
                
                # Run comprehensive audit
                audit_results = self.guard_rails.run_comprehensive_audit()
                
                # Analyze results and take actions
                self._analyze_audit_results(audit_results)
                
                # Check deployment readiness
                deployment_status = self._check_deployment_readiness(audit_results)
                
                # Handle violations and notifications
                self._handle_violations(audit_results, deployment_status)
                
                # Store results
                self.last_audit_results = audit_results
                
                # Wait for next check
                self.logger.info(f"Next audit check in {interval} seconds")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            raise
    
    def run_single_audit(self, output_file: str = None) -> Dict[str, Any]:
        """Run single audit and optionally save results"""
        self.logger.info("Running single comprehensive audit")
        
        audit_results = self.guard_rails.run_comprehensive_audit()
        deployment_status = self._check_deployment_readiness(audit_results)
        
        # Combine results
        full_results = {
            'audit_timestamp': datetime.now().isoformat(),
            'audit_results': audit_results,
            'deployment_status': deployment_status,
            'guard_rails_config': self.config
        }
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(full_results, f, indent=2)
            
            self.logger.info(f"Audit results saved to: {output_path}")
        
        # Print summary
        self._print_audit_summary(audit_results, deployment_status)
        
        return full_results
    
    def _analyze_audit_results(self, audit_results: Dict[str, Any]):
        """Analyze audit results and identify issues"""
        issues = []
        warnings = []
        
        # Check overall status
        overall_status = audit_results.get('overall_status', 'UNKNOWN')
        if overall_status in ['FAIL', 'NO_DATA']:
            issues.append(f"Overall status is {overall_status}")
        elif overall_status == 'WARNING':
            warnings.append(f"Overall status is {overall_status}")
        
        # Check pillar scores
        for pillar_id, pillar in audit_results.get('pillars', {}).items():
            score = pillar.get('score', 0)
            min_score = self.config['thresholds']['minimum_pillar_score']
            
            if score < min_score:
                issues.append(f"Pillar {pillar_id} score ({score:.1f}%) below threshold ({min_score}%)")
            
            if pillar.get('status') == 'FAIL':
                issues.append(f"Pillar {pillar_id} status is FAIL")
        
        # Check category scores
        for category_id, category in audit_results.get('categories', {}).items():
            score = category.get('score', 0)
            min_score = self.config['thresholds']['minimum_category_score']
            
            if score < min_score:
                issues.append(f"Category {category_id} score ({score:.1f}%) below threshold ({min_score}%)")
        
        # Check critical features
        critical_features = self.config['thresholds']['critical_features']
        for feature in critical_features:
            if not self._is_critical_feature_implemented(feature, audit_results):
                issues.append(f"Critical feature not implemented: {feature}")
        
        # Update violation count
        if issues:
            self.violation_count += 1
            self.logger.warning(f"Audit found {len(issues)} issues (violation #{self.violation_count})")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
        else:
            self.violation_count = 0
            self.logger.info("Audit passed - no critical issues found")
        
        if warnings:
            self.logger.info(f"Audit found {len(warnings)} warnings")
            for warning in warnings:
                self.logger.info(f"  - {warning}")
    
    def _check_deployment_readiness(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check if deployment should be blocked"""
        block_deployment = False
        reasons = []
        
        config = self.config['deployment_gates']
        
        # Check overall status
        overall_status = audit_results.get('overall_status', 'UNKNOWN')
        if overall_status in ['FAIL', 'NO_DATA']:
            block_deployment = True
            reasons.append(f"Overall status is {overall_status}")
        
        # Check critical violations
        critical_violations = audit_results.get('critical_violations', [])
        if critical_violations and config['block_on_critical_violations']:
            block_deployment = True
            reasons.append(f"Critical violations found: {len(critical_violations)}")
        
        # Check pillar requirements
        if config['require_all_pillars_pass']:
            failed_pillars = [
                pillar_id for pillar_id, pillar in audit_results.get('pillars', {}).items()
                if pillar.get('status') == 'FAIL'
            ]
            if failed_pillars:
                block_deployment = True
                reasons.append(f"Failed pillars: {', '.join(failed_pillars)}")
        
        # Check category requirements
        if config['require_all_categories_pass']:
            failed_categories = [
                cat_id for cat_id, category in audit_results.get('categories', {}).items()
                if category.get('status') == 'FAIL'
            ]
            if failed_categories:
                block_deployment = True
                reasons.append(f"Failed categories: {', '.join(failed_categories)}")
        
        # Check warning tolerance
        if not config['allow_warnings']:
            warning_components = []
            for pillar_id, pillar in audit_results.get('pillars', {}).items():
                if pillar.get('status') == 'WARNING':
                    warning_components.append(f"pillar:{pillar_id}")
            for cat_id, category in audit_results.get('categories', {}).items():
                if category.get('status') == 'WARNING':
                    warning_components.append(f"category:{cat_id}")
            
            if warning_components:
                block_deployment = True
                reasons.append(f"Warnings not allowed: {', '.join(warning_components)}")
        
        # Check violation count threshold
        max_violations = self.config['monitoring']['max_violations_before_block']
        if self.violation_count >= max_violations:
            block_deployment = True
            reasons.append(f"Violation count ({self.violation_count}) exceeded threshold ({max_violations})")
        
        return {
            'block_deployment': block_deployment,
            'reasons': reasons,
            'violation_count': self.violation_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_violations(self, audit_results: Dict[str, Any], deployment_status: Dict[str, Any]):
        """Handle violations and send notifications"""
        if deployment_status['block_deployment']:
            if not self.deployment_blocked:
                self.deployment_blocked = True
                self.logger.error("🚫 DEPLOYMENT BLOCKED")
                self.logger.error("Reasons:")
                for reason in deployment_status['reasons']:
                    self.logger.error(f"  - {reason}")
                
                # Send notifications
                self._send_notifications(audit_results, deployment_status)
                
                # Auto-block if configured
                if self.config['monitoring']['auto_block_deployment']:
                    self._create_deployment_block_file()
        else:
            if self.deployment_blocked:
                self.deployment_blocked = False
                self.logger.info("✅ DEPLOYMENT UNBLOCKED - Issues resolved")
                self._remove_deployment_block_file()
    
    def _send_notifications(self, audit_results: Dict[str, Any], deployment_status: Dict[str, Any]):
        """Send notifications about violations"""
        if not self.config['notifications']['enabled']:
            return
        
        notification_data = {
            'timestamp': datetime.now().isoformat(),
            'deployment_blocked': deployment_status['block_deployment'],
            'violation_count': self.violation_count,
            'reasons': deployment_status['reasons'],
            'overall_status': audit_results.get('overall_status'),
            'critical_violations': audit_results.get('critical_violations', [])
        }
        
        # Webhook notification
        webhook_url = self.config['notifications'].get('webhook_url')
        if webhook_url:
            try:
                import requests
                response = requests.post(webhook_url, json=notification_data, timeout=10)
                if response.status_code == 200:
                    self.logger.info("Webhook notification sent successfully")
                else:
                    self.logger.error(f"Webhook notification failed: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Webhook notification error: {e}")
        
        # Slack notification
        slack_webhook = self.config['notifications'].get('slack_webhook')
        if slack_webhook:
            try:
                import requests
                slack_message = {
                    'text': f"🚫 MediaHub Deployment Blocked",
                    'attachments': [{
                        'color': 'danger',
                        'fields': [
                            {'title': 'Status', 'value': audit_results.get('overall_status'), 'short': True},
                            {'title': 'Violations', 'value': str(self.violation_count), 'short': True},
                            {'title': 'Reasons', 'value': '\n'.join(deployment_status['reasons']), 'short': False}
                        ]
                    }]
                }
                response = requests.post(slack_webhook, json=slack_message, timeout=10)
                if response.status_code == 200:
                    self.logger.info("Slack notification sent successfully")
                else:
                    self.logger.error(f"Slack notification failed: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Slack notification error: {e}")
    
    def _create_deployment_block_file(self):
        """Create deployment block file"""
        block_file = self.app_root / '.deployment_blocked'
        block_data = {
            'blocked_at': datetime.now().isoformat(),
            'violation_count': self.violation_count,
            'reason': 'Guard rails violations detected'
        }
        
        with open(block_file, 'w') as f:
            json.dump(block_data, f, indent=2)
        
        self.logger.info(f"Created deployment block file: {block_file}")
    
    def _remove_deployment_block_file(self):
        """Remove deployment block file"""
        block_file = self.app_root / '.deployment_blocked'
        if block_file.exists():
            block_file.unlink()
            self.logger.info(f"Removed deployment block file: {block_file}")
    
    def _is_critical_feature_implemented(self, feature: str, audit_results: Dict[str, Any]) -> bool:
        """Check if critical feature is implemented"""
        # Check in pillars
        for pillar in audit_results.get('pillars', {}).values():
            if feature in pillar.get('features', {}):
                feature_data = pillar['features'][feature]
                return feature_data.get('implemented', False) and feature_data.get('accessible', False)
        
        # Check in other audit sections
        # This would be expanded based on specific feature locations
        return True  # Placeholder
    
    def _print_audit_summary(self, audit_results: Dict[str, Any], deployment_status: Dict[str, Any]):
        """Print audit summary to console"""
        print("\n" + "="*60)
        print("MEDIAHUB GUARD RAILS AUDIT SUMMARY")
        print("="*60)
        
        # Overall status
        overall_status = audit_results.get('overall_status', 'UNKNOWN')
        status_emoji = {
            'EXCELLENT': '🌟',
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌',
            'NO_DATA': '❓'
        }.get(overall_status, '❓')
        
        print(f"Overall Status: {status_emoji} {overall_status}")
        
        # Deployment status
        if deployment_status['block_deployment']:
            print(f"Deployment: 🚫 BLOCKED")
            print("Reasons:")
            for reason in deployment_status['reasons']:
                print(f"  - {reason}")
        else:
            print(f"Deployment: ✅ READY")
        
        # Pillar summary
        pillars = audit_results.get('pillars', {})
        if pillars:
            print(f"\nPillars ({len(pillars)}):")
            for pillar_id, pillar in pillars.items():
                status = pillar.get('status', 'UNKNOWN')
                score = pillar.get('score', 0)
                emoji = {'PASS': '✅', 'WARNING': '⚠️', 'FAIL': '❌'}.get(status, '❓')
                print(f"  {emoji} {pillar.get('name', pillar_id)}: {score:.1f}%")
        
        # Category summary
        categories = audit_results.get('categories', {})
        if categories:
            print(f"\nCategories ({len(categories)}):")
            for cat_id, category in categories.items():
                status = category.get('status', 'UNKNOWN')
                score = category.get('score', 0)
                emoji = {'PASS': '✅', 'WARNING': '⚠️', 'FAIL': '❌'}.get(status, '❓')
                print(f"  {emoji} {category.get('name', cat_id)}: {score:.1f}%")
        
        # Critical violations
        critical_violations = audit_results.get('critical_violations', [])
        if critical_violations:
            print(f"\nCritical Violations ({len(critical_violations)}):")
            for violation in critical_violations:
                print(f"  ❌ {violation}")
        
        print("\n" + "="*60)

def main():
    """Main entry point for guard rails monitor"""
    parser = argparse.ArgumentParser(description='MediaHub Implementation Guard Rails Monitor')
    parser.add_argument('--app-root', default='.', help='Path to MediaHub application root')
    parser.add_argument('--config', help='Path to guard rails configuration file')
    parser.add_argument('--mode', choices=['monitor', 'audit', 'check'], default='audit',
                       help='Operation mode: monitor (continuous), audit (single run), check (deployment readiness)')
    parser.add_argument('--output', help='Output file for audit results (JSON format)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize monitor
    monitor = GuardRailsMonitor(args.app_root, args.config)
    
    try:
        if args.mode == 'monitor':
            monitor.run_continuous_monitoring()
        elif args.mode == 'audit':
            results = monitor.run_single_audit(args.output)
            sys.exit(0 if results['deployment_status']['block_deployment'] == False else 1)
        elif args.mode == 'check':
            audit_results = monitor.guard_rails.run_comprehensive_audit()
            deployment_status = monitor._check_deployment_readiness(audit_results)
            
            if deployment_status['block_deployment']:
                print("❌ DEPLOYMENT BLOCKED")
                for reason in deployment_status['reasons']:
                    print(f"  - {reason}")
                sys.exit(1)
            else:
                print("✅ DEPLOYMENT READY")
                sys.exit(0)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
