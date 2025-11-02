from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
import os

class TransactionCategorizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500)
        self.classifier = MultinomialNB()
        self.is_trained = False
        
        # Load model if exists
        if os.path.exists('model.pkl'):
            self.load_model()
    
    def train(self, descriptions, categories):
        """Train the model with transaction descriptions and categories"""
        X = self.vectorizer.fit_transform(descriptions)
        self.classifier.fit(X, categories)
        self.is_trained = True
        self.save_model()
    
    def predict(self, description):
        """Predict category for a description"""
        if not self.is_trained:
            return self._rule_based_predict(description)
        
        X = self.vectorizer.transform([description])
        prediction = self.classifier.predict(X)[0]
        probability = self.classifier.predict_proba(X).max()
        
        return {
            'category': prediction,
            'confidence': float(probability)
        }
    
    def _rule_based_predict(self, description):
        """Fallback rule-based categorization"""
        desc_lower = description.lower()
        
        rules = {
            'Food & Dining': ['restaurant', 'cafe', 'food', 'lunch', 'dinner', 'starbucks'],
            'Transportation': ['uber', 'lyft', 'gas', 'fuel', 'parking', 'taxi'],
            'Shopping': ['amazon', 'mall', 'store', 'shopping'],
            'Bills & Utilities': ['electric', 'water', 'internet', 'rent', 'insurance'],
            'Entertainment': ['netflix', 'movie', 'spotify', 'game']
        }
        
        for category, keywords in rules.items():
            if any(keyword in desc_lower for keyword in keywords):
                return {'category': category, 'confidence': 0.7}
        
        return {'category': 'Other', 'confidence': 0.5}
    
    def save_model(self):
        with open('model.pkl', 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'classifier': self.classifier
            }, f)
    
    def load_model(self):
        with open('model.pkl', 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.classifier = data['classifier']
            self.is_trained = True

# Global instance
categorizer = TransactionCategorizer()