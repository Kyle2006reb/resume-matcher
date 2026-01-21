from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import io
import re
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import os

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)

class ResumeAnalyzer:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        self.fluff_patterns = [
            r'equal opportunity employer.*',
            r'we are committed to.*diversity.*',
            r'benefits include.*',
            r'our company.*culture.*',
            r'about us:.*',
            r'company overview.*',
            r'why join us.*',
            r'perks and benefits.*',
            r'we offer.*competitive.*',
        ]
        
        self.tech_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            r'\b[A-Z]{2,}\b',
            r'\b\w+\.js\b',
            r'\bC\+\+\b', r'\bC#\b',
        ]
        
    def extract_text_from_file(self, file):
        """Extract text from PDF or image"""
        file_bytes = file.read()
        file_type = file.content_type
        
        try:
            if file_type == 'application/pdf':
                # Use PyPDF2 for PDF extraction
                import PyPDF2
                pdf_file = io.BytesIO(file_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
                return text
            else:
                # For images, return error message
                return "Image upload not supported. Please upload a text-based PDF resume."
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
    def clean_job_description(self, jd_text):
        cleaned = jd_text.lower()
        for pattern in self.fluff_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        return cleaned
    
    def extract_hard_skills(self, text):
        hard_skills = set()
        
        for pattern in self.tech_patterns:
            matches = re.findall(pattern, text)
            hard_skills.update(matches)
        
        tech_keywords = [
            'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'gcp',
            'docker', 'kubernetes', 'react', 'angular', 'vue', 'node',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'git', 'ci/cd', 'agile', 'scrum', 'rest', 'api', 'graphql',
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'machine learning', 'data analysis', 'deep learning',
            'cloud computing', 'devops', 'microservices'
        ]
        
        text_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in text_lower:
                hard_skills.add(keyword)
        
        return hard_skills
    
    def extract_keywords(self, text):
        tokens = word_tokenize(text.lower())
        keywords = [
            token for token in tokens 
            if token.isalnum() and len(token) > 2 
            and token not in self.stop_words
        ]
        
        bigrams = [' '.join(keywords[i:i+2]) for i in range(len(keywords)-1)]
        trigrams = [' '.join(keywords[i:i+3]) for i in range(len(keywords)-2)]
        
        all_keywords = keywords + bigrams + trigrams
        return all_keywords
    
    def find_repeated_phrases(self, text):
        keywords = self.extract_keywords(text)
        counter = Counter(keywords)
        repeated = {k: v for k, v in counter.items() if v >= 2}
        return repeated
    
    def normalize_verbs(self, text):
        tokens = word_tokenize(text.lower())
        stemmed = [self.stemmer.stem(token) for token in tokens]
        return ' '.join(stemmed)
    
    def extract_implicit_keywords(self, text):
        implicit_map = {
            'cross functional': ['communication', 'collaboration', 'teamwork'],
            'end to end': ['project management', 'ownership', 'accountability'],
            'fast paced': ['prioritization', 'time management', 'adaptability'],
            'self starter': ['initiative', 'proactive', 'independent'],
            'stakeholder': ['communication', 'presentation', 'relationship'],
        }
        
        implicit_skills = set()
        text_lower = text.lower()
        
        for phrase, skills in implicit_map.items():
            if phrase in text_lower:
                implicit_skills.update(skills)
        
        return implicit_skills
    
    def calculate_match_score(self, resume_text, jd_text):
        jd_cleaned = self.clean_job_description(jd_text)
        
        jd_keywords = set(self.extract_keywords(jd_cleaned))
        resume_keywords = set(self.extract_keywords(resume_text.lower()))
        
        jd_hard_skills = self.extract_hard_skills(jd_cleaned)
        resume_hard_skills = self.extract_hard_skills(resume_text.lower())
        
        jd_repeated = self.find_repeated_phrases(jd_cleaned)
        jd_implicit = self.extract_implicit_keywords(jd_cleaned)
        
        matched_keywords = jd_keywords.intersection(resume_keywords)
        missing_keywords = jd_keywords - resume_keywords
        
        matched_hard_skills = jd_hard_skills.intersection(resume_hard_skills)
        missing_hard_skills = jd_hard_skills - resume_hard_skills
        
        keyword_score = (len(matched_keywords) / len(jd_keywords) * 100) if jd_keywords else 0
        hard_skills_score = (len(matched_hard_skills) / len(jd_hard_skills) * 100) if jd_hard_skills else 0
        
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([jd_cleaned, resume_text.lower()])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            coverage_score = similarity * 100
        except:
            coverage_score = 0
        
        overall_score = int(
            keyword_score * 0.4 +
            hard_skills_score * 0.4 +
            coverage_score * 0.2
        )
        
        recommendations = []
        
        if len(missing_hard_skills) > 0:
            recommendations.append(
                f"Add {min(5, len(missing_hard_skills))} missing hard skills: {', '.join(list(missing_hard_skills)[:5])}"
            )
        
        top_repeated = sorted(jd_repeated.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_repeated:
            recommendations.append(
                f"Emphasize these repeated phrases: {', '.join([k for k, v in top_repeated])}"
            )
        
        if jd_implicit:
            recommendations.append(
                f"Include implicit skills: {', '.join(list(jd_implicit)[:5])}"
            )
        
        if keyword_score < 50:
            recommendations.append(
                "Your resume is missing many key terms. Review the job description and add relevant keywords naturally."
            )
        
        if hard_skills_score < 50:
            recommendations.append(
                "Focus on adding technical skills and tools mentioned in the job description."
            )
        
        return {
            'overall_score': overall_score,
            'keyword_score': int(keyword_score),
            'hard_skills_score': int(hard_skills_score),
            'coverage_score': int(coverage_score),
            'matched_keywords': sorted(list(matched_keywords))[:30],
            'missing_keywords': sorted(list(missing_keywords))[:30],
            'matched_hard_skills': sorted(list(matched_hard_skills)),
            'missing_hard_skills': sorted(list(missing_hard_skills)),
            'recommendations': recommendations
        }

analyzer = ResumeAnalyzer()

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400
        
        if 'job_description' not in request.form:
            return jsonify({'error': 'No job description provided'}), 400
        
        resume_file = request.files['resume']
        job_description = request.form['job_description']
        
        resume_text = analyzer.extract_text_from_file(resume_file)
        
        if not resume_text.strip():
            return jsonify({'error': 'Could not extract text from resume'}), 400
        
        results = analyzer.calculate_match_score(resume_text, job_description)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))