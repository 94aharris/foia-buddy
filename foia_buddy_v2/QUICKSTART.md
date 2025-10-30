# FOIA-Buddy V2 - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd foia_buddy_v2
pip install -r requirements.txt
```

### Step 2: Set Your API Key

**Option A: Environment Variable (Recommended)**
```bash
export NVIDIA_API_KEY="nvapi-xxxxx"
```

**Option B: .env File**
```bash
cp .env.example .env
# Edit .env and add your key
```

**Option C: In the App**
- Enter the key in the sidebar when the app launches

### Step 3: Launch the App

**Using the launch script:**
```bash
./run.sh
```

**Or manually:**
```bash
streamlit run app.py
```

The app opens at: `http://localhost:8501`

## 🎯 First Demo (2 minutes)

1. **In the sidebar:**
   - Enter your NVIDIA API key (if not set in environment)
   - Select "AI Policy Documents" scenario
   - Click "🎲 Load Scenario"

2. **In the main area:**
   - Review the pre-loaded FOIA request
   - Click "🚀 Process Request"

3. **Watch the magic:**
   - See agents activate in real-time
   - Watch reasoning tokens stream live
   - Track metrics updating
   - View the coordination flow
   - Get the final report

## 🎨 What You'll See

### Real-Time Agent Coordination
- 🟢 Active agents pulse with green
- 💭 Live thinking tokens appear
- 📊 Metrics update dynamically
- 🔄 Flow diagram shows handoffs

### Agent Pipeline
1. **Coordinator** - Analyzes request and plans workflow
2. **PDFSearcher** - Finds relevant documents
3. **PDFParser** - Extracts content with multimodal understanding
4. **DocumentResearcher** - Performs semantic search
5. **ReportGenerator** - Creates comprehensive response

### Visualizations
- Agent status cards with progress
- Reasoning stream (color-coded)
- Live metrics dashboard
- Coordination flow diagram
- Execution timeline
- Decision point logs

## 📝 Try Other Scenarios

### Budget Transparency
Focus on financial documents and contracts
**Time: 1-2 minutes**

### Communications Records
Meeting minutes and correspondence
**Time: 2-3 minutes**

### Custom Request
Enter your own FOIA request text!

## 🎤 Demo Tips

For presentations:

1. **Start clean** - Reset browser if needed
2. **Load scenario** - Use pre-loaded scenarios for consistency
3. **Point out features** - Highlight reasoning tokens, coordination, decisions
4. **Show speed** - Note the 2-minute completion time
5. **Explain value** - Multi-agent transparency vs black box

## 🔧 Troubleshooting

### App won't start
- Check Python version: `python --version` (need 3.9+)
- Install dependencies: `pip install -r requirements.txt`

### API errors
- Verify API key is correct
- Check key at: https://build.nvidia.com/
- Ensure key has proper permissions

### Slow performance
- First run may be slower (model loading)
- Check internet connection
- Try a different demo scenario

### UI issues
- Clear browser cache
- Try different browser
- Check terminal for errors

## 💡 Customization

### Add Your Own Scenario

Edit `app.py`, find `DEMO_SCENARIOS`:

```python
DEMO_SCENARIOS = {
    "Your Scenario": {
        "request": "Your FOIA request...",
        "topics": ["topic1", "topic2"],
        "estimated_time": "X minutes"
    }
}
```

### Modify Agent Behavior

Edit individual agent files in `agents/`:
- `coordinator.py` - Orchestration logic
- `pdf_searcher.py` - Document discovery
- `pdf_parser.py` - Parsing behavior
- `document_researcher.py` - Search strategy
- `report_generator.py` - Report structure

### Customize Styling

Edit `ui/theme.py` to change:
- Colors (NVIDIA green theme)
- Fonts
- Card styles
- Animations

## 📚 Next Steps

- Read the full [README.md](README.md)
- Explore the agent implementations
- Try different demo scenarios
- Customize for your use case
- Add real PDF files to `sample_data/pdfs/`

## 🆘 Need Help?

- Check the code comments
- Review sample data in `sample_data/`
- Examine agent implementations in `agents/`
- Read UI component docs in `ui/`

---

**Ready to impress? Launch the app and let the agents do their thing! 🤖✨**
