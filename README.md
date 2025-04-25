# email-verifier-tool
![Logo](/assets/logo.png#gh-light-mode-only){: width="200"}



## 📋 Features

- ✅ **Dual Verification Modes**:
  - **API Mode**: Fast and accurate verification using the VerifyRight API
  - **Standalone Mode**: Independent verification using DNS and SMTP checks
  
- 📊 **Comprehensive Reporting**:
  - Filtered CSV output containing only valid emails
  - Detailed text and JSON reports with verification statistics
  - Visual charts (bar/pie) showing valid vs. invalid email ratios
  
- 🛠️ **Advanced Verification Methods**:
  - Email format validation using RFC 5322 compliant regex
  - Domain verification through MX record lookups
  - Mailbox existence checking via SMTP handshake
  
- 💻 **User Experience**:
  - Professional ASCII art banner
  - Animated progress indicators
  - Colored terminal output for better readability
  - Detailed progress tracking

## 🔧 Installation

### Prerequisites

- Python 3.6+
- Required Python packages:

```bash
pip install dnspython requests matplotlib tqdm colorama art
```

### Quick Start

1. Clone this repository or download the `email_verifier.py` file
2. Prepare your email list in a CSV file (one email per line)
3. Run the tool:

```bash
python email_verifier.py your_emails.csv
```

## 🚀 Usage

### Basic Usage

```bash
python email_verifier.py input_file.csv
```

This will verify emails in standalone mode and generate all reports in the `output` directory.

### API Mode

To use the VerifyRight API for verification:

```bash
python email_verifier.py input_file.csv --api-token YOUR_API_TOKEN --use-api
```

### Additional Options

```
--output-dir OUTPUT_DIR   Custom output directory (default: 'output')
--chart-type {bar,pie}    Type of chart to generate (default: 'bar')
--report-format {text,json,both}  Report format (default: 'both')
--no-progress            Disable progress bar
--no-animation           Disable ASCII animations
```

### Example Commands

Verify emails with pie chart output:
```bash
python email_verifier.py emails.csv --chart-type pie
```

Verify emails using API with JSON report only:
```bash
python email_verifier.py emails.csv --api-token YOUR_API_TOKEN --use-api --report-format json
```

Run in a script without animations:
```bash
python email_verifier.py emails.csv --no-animation --no-progress
```

## 📁 Output Files

The tool generates the following output files:

- `valid_emails.csv`: List of all verified valid emails
- `email_report.txt`: Text report with verification statistics
- `email_report.json`: JSON report with verification statistics
- `report.png`: Visual chart (bar or pie) showing verification results

## 📊 Verification Process

### Standalone Mode

1. **Format Check**: Validates email format using RFC 5322 compliant regex
2. **Domain Check**: Verifies if the domain has valid MX records
3. **Mailbox Check**: Attempts SMTP handshake to verify mailbox existence

### API Mode

Uses the VerifyRight API service to verify emails:
```
https://verifyright.co/verify/{email}?token={token}
```

## 🔍 Supported Input Formats

- CSV files with one email per line
- Email files (.eml) - the tool will extract all email addresses from the content

## 🔄 Integrating with Other Tools

You can easily integrate this tool into your workflow:

```bash
# Example: Verify emails and then use the valid ones in another script
python email_verifier.py customer_list.csv
python send_newsletter.py output/valid_emails.csv
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/email-verifier/issues).

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, email [theopensource212@gmail.com](mailto:your-email@example.com) or open an issue on the GitHub repository.

---

Made with ❤️ by Ilyass Basbassi
