# Sample PDFs Directory

This directory is for storing PDF documents that will be parsed using NVIDIA Parse Nemotron.

## Purpose

The Local PDF Search Agent will:
1. Search this directory for PDF files
2. Analyze filenames to determine relevance to the FOIA request
3. Pass relevant PDFs to the PDF Parser Agent
4. PDF Parser converts PDFs to markdown using NVIDIA Parse Nemotron

## Usage

Place any PDF documents you want to analyze in this directory. The system will:
- Find all `.pdf` files recursively
- Rank them by relevance to the FOIA request based on filename keywords
- Parse the most relevant PDFs (up to 20) to markdown
- Include parsed content in the final FOIA response report

## Demonstration

This demonstrates the **NVIDIA Parse Nemotron** capability for PDF-to-markdown conversion, which makes documents easier for:
- AI agents to analyze
- End-users to review
- Inclusion in final reports

## Example PDFs

Add PDF documents related to:
- Government policies
- Agency memos
- Meeting minutes
- Reports
- Email communications

The more descriptive the filename, the better the relevance matching will work.

Example good filenames:
- `ai-governance-policy-2024.pdf`
- `memo-ethics-guidelines-march-2024.pdf`
- `agency-ai-implementation-report.pdf`

## Note

The Public FOIA Search feature (which would download PDFs from foia.state.gov) is currently unavailable due to API limitations. This local PDF directory approach demonstrates the same PDF parsing capability with local files instead.
