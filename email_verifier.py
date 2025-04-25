import re
import csv
import os
import sys
import dns.resolver
import smtplib
import socket
import json
import argparse
import matplotlib.pyplot as plt
import requests
import time
from pathlib import Path
from email import parser as email_parser
from typing import List, Dict, Tuple, Union, Optional
from tqdm import tqdm
from colorama import init, Fore, Style
from art import text2art

# Initialize colorama for cross-platform colored terminal output
init()

__author__ = "Ilyass Basbassi"
__version__ = "2.0.0"

class EmailVerifier:
    def __init__(self, api_token: str = None, use_api: bool = False):
        self.api_token = api_token
        self.use_api = use_api and api_token is not None
        # RFC 5322 compliant regex pattern for email validation
        self.email_pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
        # VerifyRight API base URL
        self.api_base_url = "https://verifyright.co/verify/"
    
    def verify_format(self, email: str) -> bool:
        """Verify if the email address has a valid format using regex."""
        return bool(re.match(self.email_pattern, email))
    
    def verify_domain(self, domain: str) -> bool:
        """Check if the domain has valid MX records."""
        try:
            dns.resolver.resolve(domain, 'MX')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout):
            return False
    
    def verify_mailbox(self, email: str, domain: str) -> bool:
        """Attempt to verify mailbox existence via SMTP handshake."""
        try:
            # Get MX record for the domain
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)
            
            # Connect to SMTP server
            with smtplib.SMTP(host=mx_host, timeout=10) as server:
                server.ehlo()
                server.mail('')
                code, _ = server.rcpt(email)
                return code == 250  # 250 means success
        except (socket.gaierror, socket.timeout, smtplib.SMTPException, dns.exception.DNSException):
            # Skip silently if server blocks or other issues
            return True  # Assume valid if we can't check
    
    def verify_email_api(self, email: str) -> Dict:
        """Verify email using the VerifyRight API integration."""
        if not self.api_token:
            return {"status": False, "reason": "No API token provided"}
        
        try:
            api_url = f"{self.api_base_url}{email}?token={self.api_token}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "is_valid": data.get("status", False),
                    "reason": "Valid" if data.get("status", False) else "Invalid according to API"
                }
            else:
                return {"is_valid": False, "reason": f"API error: HTTP {response.status_code}"}
        except Exception as e:
            return {"is_valid": False, "reason": f"API error: {str(e)}"}
    
    def verify_email(self, email: str) -> Tuple[bool, str]:
        """Complete verification of an email address."""
        # Trim whitespace
        email = email.strip()
        
        # Check format
        if not self.verify_format(email):
            return False, "Invalid format"
        
        # Extract domain
        domain = email.split('@')[1]
        
        # If API token is provided and use_api is True, use API verification
        if self.use_api:
            result = self.verify_email_api(email)
            return result.get("is_valid", False), result.get("reason", "Unknown")
        
        # Check domain
        if not self.verify_domain(domain):
            return False, "Invalid domain (no MX records)"
        
        # Try SMTP verification (optional)
        try:
            if not self.verify_mailbox(email, domain):
                return False, "Invalid mailbox"
        except Exception:
            # Skip SMTP check if it fails
            pass
        
        return True, "Valid"
    
    def extract_emails_from_csv(self, file_path: str) -> List[str]:
        """Extract email addresses from a CSV file."""
        emails = []
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0].strip():  # Check if the row is not empty
                    emails.append(row[0].strip())
        return emails
    
    def extract_emails_from_email_file(self, file_path: str) -> List[str]:
        """Extract email addresses from an email file."""
        with open(file_path, 'r', encoding='utf-8') as email_file:
            email_content = email_file.read()
        
        # Parse email content
        email_message = email_parser.Parser().parsestr(email_content)
        
        # Extract content
        content = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Find all emails in content using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        return emails
    
    def process_file(self, file_path: str) -> List[str]:
        """Process input file and extract emails."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            return self.extract_emails_from_csv(file_path)
        else:  # Assume it's an email file
            return self.extract_emails_from_email_file(file_path)
    
    def verify_emails(self, emails: List[str], show_progress: bool = True) -> Tuple[List[Dict], Dict]:
        """Verify a list of emails and return results."""
        results = []
        
        valid_count = 0
        invalid_count = 0
        
        # Set up progress bar
        if show_progress:
            progress_bar = tqdm(total=len(emails), desc="Verifying emails", 
                                bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL))
        
        for email in emails:
            if not email or email.startswith('#'):  # Skip empty lines or comments
                if show_progress:
                    progress_bar.update(1)
                continue
            
            is_valid, reason = self.verify_email(email.strip())
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
            
            results.append({
                "email": email,
                "is_valid": is_valid,
                "reason": reason
            })
            
            if show_progress:
                progress_bar.update(1)
                time.sleep(0.01)  # Small delay for visual effect
        
        if show_progress:
            progress_bar.close()
        
        # Prepare summary
        total = valid_count + invalid_count
        success_rate = (valid_count / total) * 100 if total > 0 else 0
        
        summary = {
            "total_emails": total,
            "valid_emails": valid_count,
            "invalid_emails": invalid_count,
            "success_percentage": round(success_rate, 2)
        }
        
        return results, summary
    
    def save_valid_emails(self, results: List[Dict], output_file: str = "valid_emails.csv") -> None:
        """Save valid emails to a CSV file."""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Email"])
            for result in results:
                if result["is_valid"]:
                    writer.writerow([result["email"]])
    
    def generate_text_report(self, summary: Dict, output_file: str = "email_report.txt") -> None:
        """Generate a text report with verification summary."""
        with open(output_file, 'w', encoding='utf-8') as report_file:
            report_file.write("Email Verification Report\n")
            report_file.write("=======================\n\n")
            report_file.write(f"Total emails: {summary['total_emails']}\n")
            report_file.write(f"Valid emails: {summary['valid_emails']}\n")
            report_file.write(f"Invalid emails: {summary['invalid_emails']}\n")
            report_file.write(f"Success rate: {summary['success_percentage']}%\n")
            report_file.write(f"\nVerification mode: {'API' if self.use_api else 'Standalone'}\n")
            report_file.write(f"Generated by: Email Verifier v{__version__}\n")
            report_file.write(f"Developer: {__author__}\n")
    
    def generate_json_report(self, summary: Dict, output_file: str = "email_report.json") -> None:
        """Generate a JSON report with verification summary."""
        report_data = summary.copy()
        report_data["verification_mode"] = "API" if self.use_api else "Standalone"
        report_data["generator"] = f"Email Verifier v{__version__}"
        report_data["developer"] = __author__
        
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(report_data, json_file, indent=4)
    
    def generate_chart(self, summary: Dict, chart_type: str = "bar", output_file: str = "report.png") -> None:
        """Generate a chart visualization of the results."""
        labels = ['Valid', 'Invalid']
        values = [summary['valid_emails'], summary['invalid_emails']]
        colors = ['#4CAF50', '#F44336']  # Green for valid, red for invalid
        
        plt.figure(figsize=(10, 6))
        plt.title('Email Verification Results', fontsize=16)
        
        if chart_type.lower() == 'pie':
            plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.legend(title="Email Status")
        else:  # Default to bar chart
            bars = plt.bar(labels, values, color=colors)
            plt.xlabel('Email Status')
            plt.ylabel('Count')
            
            # Add count labels on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                         f'{height}', ha='center', va='bottom')
            
            # Add percentage labels
            total = sum(values)
            for i, bar in enumerate(bars):
                height = bar.get_height()
                percentage = (height / total) * 100 if total > 0 else 0
                plt.text(bar.get_x() + bar.get_width()/2., height/2,
                         f'{percentage:.1f}%', ha='center', va='center',
                         color='white', fontweight='bold')
        
        # Add mode info
        mode_text = f"Mode: {'API' if self.use_api else 'Standalone'}"
        plt.figtext(0.95, 0.01, mode_text, horizontalalignment='right')
        
        # Add developer info
        dev_text = f"Developer: {__author__}"
        plt.figtext(0.01, 0.01, dev_text, horizontalalignment='left')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()


def display_ascii_banner():
    """Display ASCII art banner."""
    banner = text2art("Email Verifier", font="small")
    print(f"{Fore.CYAN}{banner}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Version: {__version__}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Developer: {__author__}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'-' * 60}{Style.RESET_ALL}")


def animated_spinner(seconds=3):
    """Display an animated spinner for the specified number of seconds."""
    spinner = ['|', '/', '-', '\\']
    start_time = time.time()
    i = 0
    
    while time.time() - start_time < seconds:
        sys.stdout.write(f"\r{Fore.CYAN}Loading {spinner[i % len(spinner)]}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    
    sys.stdout.write("\r" + " " * 20 + "\r")  # Clear the spinner line
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description='Email Verification Tool')
    parser.add_argument('input_file', help='Input file (CSV or email file)')
    parser.add_argument('--api-token', help='API token for VerifyRight email verification service')
    parser.add_argument('--use-api', action='store_true', help='Use API for verification instead of standalone mode')
    parser.add_argument('--output-dir', default='output', help='Output directory for results')
    parser.add_argument('--chart-type', default='bar', choices=['bar', 'pie'], help='Type of chart to generate')
    parser.add_argument('--report-format', default='both', choices=['text', 'json', 'both'], help='Report format')
    parser.add_argument('--no-progress', action='store_true', help='Disable progress bar')
    parser.add_argument('--no-animation', action='store_true', help='Disable ASCII animations')
    
    args = parser.parse_args()
    
    # Show ASCII banner
    if not args.no_animation:
        display_ascii_banner()
        animated_spinner(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create EmailVerifier instance
    verifier = EmailVerifier(api_token=args.api_token, use_api=args.use_api)
    
    try:
        # Process input file
        print(f"{Fore.CYAN}Processing file: {args.input_file}{Style.RESET_ALL}")
        if not args.no_animation:
            animated_spinner(1)
            
        emails = verifier.process_file(args.input_file)
        
        # Verify emails
        print(f"{Fore.CYAN}Verifying {len(emails)} emails...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Mode: {'API' if args.use_api else 'Standalone'}{Style.RESET_ALL}")
        
        # Only show progress bar if not disabled
        results, summary = verifier.verify_emails(emails, show_progress=not args.no_progress)
        
        # Save valid emails
        output_csv = os.path.join(args.output_dir, "valid_emails.csv")
        verifier.save_valid_emails(results, output_csv)
        print(f"{Fore.GREEN}Valid emails saved to: {output_csv}{Style.RESET_ALL}")
        
        # Generate reports
        if args.report_format in ['text', 'both']:
            output_txt = os.path.join(args.output_dir, "email_report.txt")
            verifier.generate_text_report(summary, output_txt)
            print(f"{Fore.GREEN}Text report saved to: {output_txt}{Style.RESET_ALL}")
        
        if args.report_format in ['json', 'both']:
            output_json = os.path.join(args.output_dir, "email_report.json")
            verifier.generate_json_report(summary, output_json)
            print(f"{Fore.GREEN}JSON report saved to: {output_json}{Style.RESET_ALL}")
        
        # Generate chart
        output_chart = os.path.join(args.output_dir, "report.png")
        verifier.generate_chart(summary, args.chart_type, output_chart)
        print(f"{Fore.GREEN}Chart saved to: {output_chart}{Style.RESET_ALL}")
        
        # Print summary
        print(f"\n{Fore.CYAN}Verification Summary:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total emails: {summary['total_emails']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Valid emails: {summary['valid_emails']}{Style.RESET_ALL}")
        print(f"{Fore.RED}Invalid emails: {summary['invalid_emails']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Success rate: {summary['success_percentage']}%{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())