#!/usr/bin/env python3
"""
Quiz application that reads questions from JSON file and asks them sequentially.
User can skip questions or view solutions.
"""

import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path
from datetime import datetime
import os


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Review Quiz")
        self.root.geometry("950x600")
        self.root.resizable(True, False)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configure colors
        self.bg_color = "#f0f0f0"
        self.header_color = "#2c3e50"
        self.accent_color = "#3498db"
        self.text_color = "#333333"
        self.success_color = "#27ae60"
        self.warning_color = "#e74c3c"
        
        self.root.configure(bg=self.bg_color)
        
        # Data
        self.questions_data = []
        self.current_question_index = 0
        self.current_topic_index = 0
        self.showing_solution = False
        self.stats = {
            "total": 0,
            "skipped": 0,
            "answered": 0
        }
        
        # Load data
        self.load_questions()
        
        if not self.questions_data:
            messagebox.showerror("Error", "No questions found. Please run popup_review.py first.")
            self.root.destroy()
            return
        
        # Count total questions
        for topic_data in self.questions_data:
            self.stats["total"] += len(topic_data["items"])
        
        # Create UI
        self.create_widgets()
        self.show_question()
    
    def load_questions(self):
        """Load questions from today's JSON file."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"review_{today}.json"
        filepath = Path(filename)
        
        if not filepath.exists():
            # Try to find the most recent review file
            review_files = list(Path(".").glob("review_*.json"))
            if review_files:
                filepath = sorted(review_files)[-1]
            else:
                return
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.questions_data = data.get("questions", [])
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading file: {e}")
    
    def create_widgets(self):
        """Create the UI elements."""
        # Header frame
        header_frame = tk.Frame(self.root, bg=self.header_color)
        header_frame.pack(fill=tk.X)
        
        self.title_label = tk.Label(
            header_frame,
            text="",
            font=("Segoe UI", 16, "bold"),
            bg=self.header_color,
            fg="white",
            wraplength=850,
            justify=tk.CENTER,
            pady=15
        )
        self.title_label.pack()
        
        self.progress_label = tk.Label(
            header_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.header_color,
            fg="#ecf0f1",
            wraplength=850,
            justify=tk.CENTER,
            pady=15
        )
        self.progress_label.pack()
        
        # Content frame
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Question/Solution label frame
        label_frame = tk.Frame(content_frame, bg="white", relief=tk.FLAT, bd=1)
        label_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.content_label = tk.Label(
            label_frame,
            text="",
            font=("Segoe UI", 12),
            bg="white",
            fg=self.text_color,
            wraplength=850,
            justify=tk.LEFT,
            padx=15,
            pady=15
        )
        self.content_label.pack(fill=tk.BOTH, expand=True)
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))
        
        # First row of buttons
        button_row1 = tk.Frame(button_frame, bg=self.bg_color)
        button_row1.pack(fill=tk.X, pady=(0, 10))
        
        self.solution_button = tk.Button(
            button_row1,
            text="💡 Show Solution",
            command=self.show_solution,
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor="hand2"
        )
        self.solution_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.skip_button = tk.Button(
            button_row1,
            text="⊘ Skip",
            command=self.skip_question,
            font=("Segoe UI", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor="hand2"
        )
        self.skip_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Second row of buttons
        button_row2 = tk.Frame(button_frame, bg=self.bg_color)
        button_row2.pack(fill=tk.X)
        
        self.next_button = tk.Button(
            button_row2,
            text="→ Next Question",
            command=self.next_question,
            font=("Segoe UI", 10, "bold"),
            bg=self.success_color,
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.next_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.quit_button = tk.Button(
            button_row2,
            text="✕ Quit",
            command=self.quit_app,
            font=("Segoe UI", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor="hand2"
        )
        self.quit_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def get_current_question(self):
        """Get the current question data."""
        if self.current_topic_index >= len(self.questions_data):
            return None
        
        topic_data = self.questions_data[self.current_topic_index]
        items = topic_data["items"]
        
        if self.current_question_index >= len(items):
            return None
        
        return {
            "topic": topic_data["topic"],
            "question": items[self.current_question_index]["question"],
            "solution": items[self.current_question_index]["solution"]
        }
    
    def show_question(self):
        """Display the current question."""
        self.showing_solution = False
        
        question_data = self.get_current_question()
        if not question_data:
            self.show_quiz_complete()
            return
        
        # Update title
        self.title_label.config(text=f"Topic: {question_data['topic']}")
        
        # Update progress
        total_asked = sum(
            len(self.questions_data[i]["items"])
            for i in range(self.current_topic_index)
        ) + self.current_question_index + 1
        
        self.progress_label.config(
            text=f"Question {total_asked} of {self.stats['total']}"
        )
        
        # Show question
        self.content_label.config(text=question_data["question"])
        
        # Update buttons
        self.solution_button.config(state=tk.NORMAL, text="Show Solution")
        self.skip_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
    
    def show_solution(self):
        """Display the solution for the current question."""
        if self.showing_solution:
            return
        
        question_data = self.get_current_question()
        if not question_data:
            return
        
        self.showing_solution = True
        
        # Show solution
        self.content_label.config(text=f"Solution:\n\n{question_data['solution']}")
        
        # Update buttons
        self.solution_button.config(state=tk.DISABLED)
        self.skip_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.NORMAL)
        
        self.stats["answered"] += 1
    
    def skip_question(self):
        """Skip the current question."""
        self.stats["skipped"] += 1
        self.next_question()
    
    def next_question(self):
        """Move to the next question."""
        self.current_question_index += 1
        
        # Check if we've finished all questions in this topic
        if self.current_topic_index < len(self.questions_data):
            topic_data = self.questions_data[self.current_topic_index]
            if self.current_question_index >= len(topic_data["items"]):
                self.current_question_index = 0
                self.current_topic_index += 1
        
        self.show_question()
    
    def show_quiz_complete(self):
        """Show the completion summary."""
        self.title_label.config(text="🎉 Quiz Complete!")
        
        summary = f"""✅ Quiz Session Summary
{'─'*40}

📊 Total Questions: {self.stats['total']}
✓ Questions Answered: {self.stats['answered']}
⊘ Questions Skipped: {self.stats['skipped']}

Great job reviewing today's topics!
        """
        
        self.content_label.config(text=summary)
        
        # Disable all buttons except quit
        self.solution_button.config(state=tk.DISABLED)
        self.skip_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.progress_label.config(text="")
    
    def quit_app(self):
        """Quit the application."""
        self.root.destroy()


def main():
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
