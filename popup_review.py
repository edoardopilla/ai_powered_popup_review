#!/usr/bin/env python3
"""
Desktop popup window asking about topics to review today.
Uses OpenAI-compatible API to generate questions for each topic.
Stores user input in a JSON file with AI-generated questions and solutions.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
from dotenv import load_dotenv
import json
from pathlib import Path
import requests
import os
import re
import time
import glob

load_dotenv()


def get_api_credentials(root):
    """Get API endpoint and key from user or environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    api_endpoint = os.getenv("OPENAI_API_ENDPOINT", "https://api.openai.com/v1")
    
    if not api_key:
        api_key = simpledialog.askstring(
            "API Configuration",
            "Enter your OpenAI API key:",
            parent=root,
            show="*"
        )
        if not api_key:
            return None, None
    
    return api_key, api_endpoint


def generate_questions_for_topic(api_key, api_endpoint, topic):
    """Call LLM API to generate questions for a topic."""
    url = f"{api_endpoint}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Given the following user prompt, generate 5 questions that test whether the user has understood the given topic/concept. Also provide the correct answer/solution for each question. Format the response as a JSON array with objects containing 'question' and 'solution' fields. Only return valid JSON, no additional text."
            },
            {
                "role": "user",
                "content": f"Topic: {topic}"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Extract and parse JSON from response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            items = json.loads(json_match.group())
            return items
        
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return []
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing API response: {e}")
        return []


def parse_topics(topics_string):
    """Parse comma-separated topics into a list."""
    return [topic.strip() for topic in topics_string.split(",") if topic.strip()]


def save_to_json(topics_list, questions_data):
    """Save the review data to both a daily JSON file and cumulative history file."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Delete previous daily JSON files (keep only today's and never delete review_history.json)
    today_filename = f"review_{today}.json"
    for filepath in glob.glob("review_*.json"):
        if filepath != "review_history.json" and filepath != today_filename:
            try:
                Path(filepath).unlink()
                print(f"Deleted previous daily file: {filepath}")
            except Exception as e:
                print(f"Warning: Could not delete {filepath}: {e}")
    
    daily_data = {
        "date": today,
        "topics": topics_list,
        "questions": questions_data
    }
    
    # Save to daily file
    daily_filename = f"review_{today}.json"
    daily_filepath = Path(daily_filename)
    
    with open(daily_filepath, "w", encoding="utf-8") as f:
        json.dump(daily_data, f, indent=2, ensure_ascii=False)
    
    # Save/append to history file for long-term retention
    history_filename = "review_history.json"
    history_filepath = Path(history_filename)
    
    # Load existing history or create new list
    if history_filepath.exists():
        with open(history_filepath, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []
    
    # Check if entry for today exists
    today_entry_index = None
    for i, entry in enumerate(history):
        if entry.get("date") == today:
            today_entry_index = i
            break
    
    # If entry for today exists, merge questions; otherwise append as new entry
    if today_entry_index is not None:
        # Merge questions from multiple runs on the same day
        existing_entry = history[today_entry_index]
        existing_entry["topics"].extend(topics_list)
        existing_entry["questions"].extend(questions_data)
        # Remove duplicates from topics
        existing_entry["topics"] = list(dict.fromkeys(existing_entry["topics"]))
    else:
        # New date, append entry
        history.append(daily_data)
    
    # Save history
    with open(history_filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    return daily_filepath, history_filepath


def show_review_popup():
    """Display a popup window asking for topics to review."""
    # Create root window
    root = tk.Tk()
    root.title("Daily Review Topics")
    root.geometry("850x500")
    root.resizable(True, False)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Configure colors and styles
    bg_color = "#f0f0f0"
    header_color = "#2c3e50"
    accent_color = "#3498db"
    text_color = "#333333"
    
    root.configure(bg=bg_color)
    
    # Header frame
    header_frame = tk.Frame(root, bg=header_color)
    header_frame.pack(fill=tk.X)
    
    title_label = tk.Label(
        header_frame,
        text="📚 Daily Review Topics",
        font=("Segoe UI", 18, "bold"),
        bg=header_color,
        fg="white",
        pady=15,
        wraplength=750,
        justify=tk.CENTER
    )
    title_label.pack()
    
    subtitle_label = tk.Label(
        header_frame,
        text="What topics should be reviewed today?",
        font=("Segoe UI", 10),
        bg=header_color,
        fg="#ecf0f1",
        pady=5,
        wraplength=750,
        justify=tk.CENTER
    )
    subtitle_label.pack()
    
    # Main content frame
    content_frame = tk.Frame(root, bg=bg_color)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    instruction_label = tk.Label(
        content_frame,
        text="Enter topics separated by commas (e.g., Python, Git, Design Patterns)",
        font=("Segoe UI", 9),
        bg=bg_color,
        fg=text_color,
        wraplength=750,
        justify=tk.LEFT
    )
    instruction_label.pack(anchor=tk.W, pady=10)
    
    # Text input frame
    input_frame = tk.Frame(content_frame, bg="white", relief=tk.FLAT, bd=1)
    input_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    topics_text = tk.Text(
        input_frame,
        font=("Segoe UI", 11),
        fg=text_color,
        bg="white",
        relief=tk.FLAT,
        wrap=tk.WORD,
        padx=10,
        pady=10,
        height=6
    )
    topics_text.pack(fill=tk.BOTH, expand=True)
    
    # Status label
    status_label = tk.Label(
        content_frame,
        text="",
        font=("Segoe UI", 9),
        bg=bg_color,
        fg="#e74c3c",
        wraplength=750,
        justify=tk.LEFT
    )
    status_label.pack(anchor=tk.W, pady=10)
    
    # Button frame
    button_frame = tk.Frame(root, bg=bg_color)
    button_frame.pack(fill=tk.X, padx=20, pady=20)
    
    def on_submit():
        topics_input = topics_text.get("1.0", tk.END).strip()
        
        if not topics_input:
            status_label.config(text="❌ Please enter at least one topic", fg="#e74c3c")
            return
        
        topics_list = parse_topics(topics_input)
        
        if not topics_list:
            status_label.config(text="❌ No valid topics found", fg="#e74c3c")
            return
        
        # Disable buttons during processing
        submit_btn.config(state=tk.DISABLED)
        cancel_btn.config(state=tk.DISABLED)
        status_label.config(text="🔄 Processing...", fg="#3498db")
        root.update()
        
        # Get API credentials
        api_key, api_endpoint = get_api_credentials(root)
        if not api_key or not api_endpoint:
            status_label.config(text="❌ API credentials are required", fg="#e74c3c")
            submit_btn.config(state=tk.NORMAL)
            cancel_btn.config(state=tk.NORMAL)
            return
        
        # Generate questions for each topic using LLM
        questions_data = []
        
        for i, topic in enumerate(topics_list):
            status_label.config(
                text=f"🔄 Generating questions for '{topic}'... ({i+1}/{len(topics_list)})",
                fg="#3498db"
            )
            root.update()
            
            items = generate_questions_for_topic(api_key, api_endpoint, topic)
            
            if items:
                questions_data.append({
                    "topic": topic,
                    "items": items
                })
            else:
                status_label.config(
                    text=f"⚠️ Could not generate questions for '{topic}'. Skipping...",
                    fg="#f39c12"
                )
                root.update()
                time.sleep(1)
        
        # Save to JSON file
        daily_filepath, history_filepath = save_to_json(topics_list, questions_data)
        
        status_label.config(text="✅ Success! Review data saved.", fg="#27ae60")
        root.update()
        
        messagebox.showinfo(
            "Review Data Generated and Saved",
            f"Review topics and AI-generated questions saved to:\n\n"
            f"📅 Daily: {daily_filepath}\n"
            f"📊 History: {history_filepath}"
        )
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data saved to {daily_filepath}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] History updated: {history_filepath}")
        
        root.destroy()
    
    def on_cancel():
        print("User cancelled the popup.")
        root.destroy()
    
    submit_btn = tk.Button(
        button_frame,
        text="✓ Generate Review Questions",
        font=("Segoe UI", 11, "bold"),
        bg=accent_color,
        fg="white",
        relief=tk.FLAT,
        padx=20,
        pady=10,
        cursor="hand2",
        command=on_submit
    )
    submit_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    cancel_btn = tk.Button(
        button_frame,
        text="✕ Cancel",
        font=("Segoe UI", 11),
        bg="#95a5a6",
        fg="white",
        relief=tk.FLAT,
        padx=20,
        pady=10,
        cursor="hand2",
        command=on_cancel
    )
    cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Set focus to text input
    topics_text.focus()
    
    root.mainloop()


if __name__ == "__main__":
    show_review_popup()
