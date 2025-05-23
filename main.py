from flask import Flask, request, jsonify
from flask_cors import CORS
from recipe_scrapers import scrape_html
from urllib.parse import urlparse
from urllib.request import urlopen
import os
from dotenv import load_dotenv
from ingredient_parser import parse_ingredient

load_dotenv()

app = Flask(__name__)

# Configure CORS with allowed origins from .env
allowed_origins = os.getenv('ALLOWED_ORIGINS').split(',')
CORS(app, resources={r"/*": {"origins": allowed_origins}})

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

@app.route('/scrape-recipe', methods=['POST'])
def scrape_recipe():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Validate URL format
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return jsonify({'error': 'Invalid URL format'}), 400
            
        # Scrape the recipe
        html = urlopen(url).read().decode("utf-8")
        scraper = scrape_html(html, org_url=url)
        
        # Convert to JSON
        recipe_data = scraper.to_json()
        parsed_ingredients = []
        for ingredient in recipe_data['ingredients']:
            try:
                parsed = parse_ingredient(ingredient)
                # Convert parsed ingredient to dict to make it JSON serializable
                parsed_dict = {
                    'name': parsed.name,
                    'size': parsed.size,
                    'amount': [{
                        'quantity': float(amt.quantity) if amt.quantity else None,
                        'unit': str(amt.unit) if amt.unit else None
                    } for amt in parsed.amount],
                    'preparation': parsed.preparation,
                    'comment': parsed.comment,
                    'purpose': parsed.purpose,
                    'original': ingredient
                }
                parsed_ingredients.append(parsed_dict)
            except Exception as e:
                print(f"Error parsing ingredient: {e}")
                parsed_ingredients.append({'original': ingredient})  # Keep original ingredient on parse failure
        recipe_data['parsed_ingredients'] = parsed_ingredients
        
        return jsonify(recipe_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
