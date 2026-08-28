# ==========================================
# CHAT UTILITIES - OLLAMA AI ONLY
# ==========================================

from config import Config
import requests
import json
import time

class OllamaChat:
    def __init__(self):
        """Initialize Ollama AI"""
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_models = ["llama3.2:1b", "llama2", "mistral", "phi", "gemma"]
        self.ollama_available_model = None
        
        # Check which Ollama models are available
        self._check_ollama_models()

    def _check_ollama_models(self):
        """Check which Ollama models are available"""
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                available_models = [model['name'] for model in data.get('models', [])]
                print(f"📦 Available Ollama models: {available_models}")
                
                # Find the first available model from our list
                for model in self.ollama_models:
                    if model in available_models or any(model in m for m in available_models):
                        self.ollama_available_model = model
                        print(f"✅ Using Ollama model: {model}")
                        break
                
                if not self.ollama_available_model:
                    print("⚠️ No Ollama models found. Please run: ollama pull llama2")
            else:
                print("⚠️ Ollama is not responding")
        except Exception as e:
            print(f"⚠️ Ollama not available: {e}")

    def get_response_with_all_students(self, message, all_students_data, image_file=None):
        """Get response with all students data - Ollama only"""
        return self._get_ollama_response(message, all_students_data, image_file)

    def get_response(self, message, student_data, image_file=None):
        """Get response for single student - Ollama only"""
        return self._get_ollama_student_response(message, student_data, image_file)

    # ==========================================
    # OLLAMA API CALLS
    # ==========================================
    
    def _get_ollama_response(self, message, all_students_data, image_file=None):
        """Get response from Ollama"""
        
        # Check if we have an available model
        if not self.ollama_available_model:
            return "⚠️ No Ollama model available. Please run: ollama pull llama2"
        
        try:
            prompt = f"""
You are an AI Assistant for a Student Monitoring System.
You have access to ALL student data.

{all_students_data}

USER QUESTION: {message}

Answer clearly and helpfully. Use the data provided.
"""
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_available_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response from Ollama.')
            elif response.status_code == 404:
                return f"⚠️ Ollama model '{self.ollama_available_model}' not found. Please run: ollama pull {self.ollama_available_model}"
            else:
                return f"⚠️ Ollama Error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "⚠️ Ollama is not running. Please start it with 'ollama serve'"
        except Exception as e:
            return f"⚠️ Ollama Error: {str(e)}"

    def _get_ollama_student_response(self, message, student_data, image_file=None):
        """Get student-specific response from Ollama"""
        
        # Check if we have an available model
        if not self.ollama_available_model:
            return "⚠️ No Ollama model available. Please run: ollama pull llama2"
        
        try:
            prompt = f"""
You are an AI Assistant for a Student Monitoring System.
Be friendly, professional, and helpful.

STUDENT DATA:
- Name: {student_data.get('name', 'Not set') if student_data else 'Not available'}
- Roll Number: {student_data.get('roll_number', 'Not set') if student_data else 'Not available'}
- CGPA: {student_data.get('cgpa', 'Not set') if student_data else 'Not available'}
- Attendance: {student_data.get('attendance_percentage', 'Not set')}% if student_data else 'Not available'

USER QUESTION: {message}

Answer naturally and helpfully.
"""
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_available_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response from Ollama.')
            elif response.status_code == 404:
                return f"⚠️ Ollama model '{self.ollama_available_model}' not found. Please run: ollama pull {self.ollama_available_model}"
            else:
                return f"⚠️ Ollama Error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "⚠️ Ollama is not running. Please start it with 'ollama serve'"
        except Exception as e:
            return f"⚠️ Ollama Error: {str(e)}"