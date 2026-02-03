"""
Optimized prompts for ALL 14 CJ Dropshipping categories.
Each category gets a tailored prompt for maximum Gemini success rate.
"""

from cj_category_system import CJCategory, SubCategory, CategoryResult


class CJPromptBuilder:
    """Build category-specific prompts for CJ products"""
    
    def build_prompt(self, product: dict, category_result: CategoryResult) -> str:
        """Build optimized prompt based on detected category"""
        
        title = product.get('title', 'Product')
        category = category_result.main_category
        
        # Route to category-specific prompt builder
        builders = {
            CJCategory.WOMENS_CLOTHING: self._womens_clothing_prompt,
            CJCategory.MENS_CLOTHING: self._mens_clothing_prompt,
            CJCategory.TOYS_KIDS_BABIES: self._kids_toys_prompt,
            CJCategory.JEWELRY_WATCHES: self._jewelry_prompt,
            CJCategory.BAGS_SHOES: self._bags_shoes_prompt,
            CJCategory.HEALTH_BEAUTY_HAIR: self._beauty_prompt,
            CJCategory.PET_SUPPLIES: self._pet_prompt,
            CJCategory.CONSUMER_ELECTRONICS: self._electronics_prompt,
            CJCategory.PHONES_ACCESSORIES: self._phone_prompt,
            CJCategory.COMPUTER_OFFICE: self._computer_prompt,
            CJCategory.HOME_GARDEN_FURNITURE: self._home_prompt,
            CJCategory.HOME_IMPROVEMENT: self._diy_prompt,
            CJCategory.SPORTS_OUTDOORS: self._sports_prompt,
            CJCategory.AUTOMOBILES_MOTORCYCLES: self._auto_prompt,
            CJCategory.GENERAL: self._general_prompt,
        }
        
        builder = builders.get(category, self._general_prompt)
        return builder(title, category_result)
    
    # =========================================================================
    # WOMEN'S CLOTHING - Female model wearing the item
    # =========================================================================
    
    def _womens_clothing_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        
        shot_types = {
            SubCategory.WOMENS_DRESS: "Full body shot, model standing elegantly",
            SubCategory.WOMENS_TOP: "3/4 shot from waist up",
            SubCategory.WOMENS_BOTTOM: "Full body showing pants/skirt fit",
            SubCategory.WOMENS_OUTERWEAR: "Full body, jacket open or closed",
            SubCategory.WOMENS_SWIMWEAR: "Full body, confident beach pose",
            SubCategory.WOMENS_ACTIVEWEAR: "Dynamic fitness-ready pose",
        }
        
        return f"""Professional fashion photography for e-commerce.

PRODUCT: {title}

SHOT: {shot_types.get(sub, "Natural pose showcasing the garment")}

MODEL: Professional female model, age 25-35
- Confident, elegant pose
- Natural body proportions
- Face can be cropped at chin level

STYLING:
- Clean, minimal styling
- Garment is the focus
- Appropriate complementary pieces

PHOTOGRAPHY:
- Clean white or light gray studio background
- Professional soft lighting
- Sharp focus on fabric texture
- High-end fashion catalog quality (Zara, H&M style)
- Accurate colors

Generate a photorealistic fashion product image."""
    
    # =========================================================================
    # MEN'S CLOTHING - Male model wearing the item
    # =========================================================================
    
    def _mens_clothing_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        
        shot_types = {
            SubCategory.MENS_SHIRT: "3/4 shot or upper body",
            SubCategory.MENS_PANTS: "Full body showing fit",
            SubCategory.MENS_SUIT: "Full body, professional stance",
            SubCategory.MENS_OUTERWEAR: "Full body showing jacket",
            SubCategory.MENS_ACTIVEWEAR: "Dynamic active pose",
        }
        
        return f"""Professional men's fashion photography for e-commerce.

PRODUCT: {title}

SHOT: {shot_types.get(sub, "Natural pose showcasing the garment")}

MODEL: Professional male model, age 28-40
- Confident, relaxed pose
- Modern menswear editorial style
- Natural body language

STYLING:
- Clean, contemporary styling
- Focus on the garment
- Simple complementary pieces

PHOTOGRAPHY:
- Clean white or light gray studio background
- Professional lighting
- Sharp fabric detail
- Men's fashion catalog quality
- Accurate colors

Generate a photorealistic men's fashion product image."""
    
    # =========================================================================
    # TOYS, KIDS & BABIES
    # =========================================================================
    
    def _kids_toys_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        
        if sub in [SubCategory.BABY_CLOTHING, SubCategory.KIDS_CLOTHING]:
            return f"""Children's fashion photography for e-commerce.

PRODUCT: {title}

MODEL: Child model, age 4-10
- Cheerful, playful expression
- Natural, age-appropriate pose
- Focus on the clothing

SETTING:
- Bright, colorful studio
- Fun, playful atmosphere

PHOTOGRAPHY:
- Bright, even lighting
- Cheerful mood
- Children's catalog quality
- Wholesome presentation

Generate a cheerful children's fashion image."""
        
        elif sub == SubCategory.TOYS:
            return f"""Toy product photography for e-commerce.

PRODUCT: {title}

PRESENTATION:
- Toy displayed attractively
- Show play value and features
- Bright, fun presentation
- NO children in image

BACKGROUND:
- Fun, colorful background
- OR clean white for clarity

PHOTOGRAPHY:
- Bright, cheerful lighting
- Sharp detail on features
- Toy catalog quality
- Exciting, appealing

Generate an exciting toy product image."""
        
        else:  # Baby gear
            return f"""Baby product photography for e-commerce.

PRODUCT: {title}

PRESENTATION:
- Product displayed safely
- Show features and functionality
- Clean, trustworthy aesthetic
- NO babies in image

BACKGROUND:
- Soft, pastel nursery setting
- OR clean white background

PHOTOGRAPHY:
- Soft, warm lighting
- Clear detail on features
- Baby product catalog quality

Generate a professional baby product image."""
    
    # =========================================================================
    # JEWELRY & WATCHES
    # =========================================================================
    
    def _jewelry_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        
        if sub in [SubCategory.NECKLACE, SubCategory.EARRINGS, SubCategory.BRACELET]:
            body_part = {
                SubCategory.NECKLACE: "neck and collarbone area",
                SubCategory.EARRINGS: "ear profile, side angle",
                SubCategory.BRACELET: "elegant wrist and hand",
            }
            
            return f"""Luxury jewelry photography for e-commerce.

PRODUCT: {title}

MODEL: Elegant female model wearing the jewelry
- Focus on {body_part.get(sub, "jewelry display")}
- Sophisticated, tasteful presentation
- Jewelry is the hero

PHOTOGRAPHY:
- Dramatic lighting to show sparkle
- Dark gradient or elegant background
- Sharp detail on metalwork
- Luxury brand quality (Tiffany style)

Generate an elegant jewelry product image."""
        
        else:  # Ring, watch - standalone
            return f"""Luxury jewelry/watch photography for e-commerce.

PRODUCT: {title}

PRESENTATION:
- Product on elegant display
- Velvet, marble, or stand
- Dramatic spotlight
- NO hands or models

BACKGROUND:
- Dark gradient or luxury setting
- Elegant, sophisticated mood

PHOTOGRAPHY:
- Dramatic spotlight lighting
- Extreme detail and sharpness
- Luxury catalog quality

Generate a luxurious jewelry product image."""
    
    # =========================================================================
    # BAGS & SHOES
    # =========================================================================
    
    def _bags_shoes_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        gender = result.model_gender or "female"
        
        if sub in [SubCategory.HANDBAG, SubCategory.BACKPACK]:
            return f"""Professional bag photography for e-commerce.

PRODUCT: {title}

MODEL: Stylish {gender} model with the bag
- Natural pose, bag at hip or shoulder
- Fashionable styling
- Bag is the focus

PHOTOGRAPHY:
- Clean studio background
- Professional lighting
- Sharp detail on materials
- Accessories catalog quality

Generate a professional bag product image."""
        
        elif sub in [SubCategory.WOMENS_SHOES, SubCategory.MENS_SHOES]:
            return f"""Professional shoe photography for e-commerce.

PRODUCT: {title}

PRESENTATION:
- Shoes displayed as pair
- 45-degree angle
- Show design and quality
- NO feet or models

BACKGROUND:
- Clean white background
- OR elegant gradient

PHOTOGRAPHY:
- Professional lighting
- Sharp material detail
- Shoe catalog quality

Generate a professional shoe product image."""
        
        else:  # Wallet, accessories
            return f"""Accessories photography for e-commerce.

PRODUCT: {title}

PRESENTATION:
- Product elegantly displayed
- Show material and details
- Clean, sophisticated

PHOTOGRAPHY:
- Studio background
- Professional lighting
- Sharp detail
- Accessories catalog quality

Generate a professional accessories image."""
    
    # =========================================================================
    # HEALTH, BEAUTY & HAIR - Product focus, elegant
    # =========================================================================
    
    def _beauty_prompt(self, title: str, result: CategoryResult) -> str:
        return f"""Luxury beauty product photography.

PRODUCT: {title}

PRESENTATION:
- Product as hero, elegantly displayed
- Show packaging details
- NO human models

BACKGROUND:
- Clean white, marble, or soft gradient
- May include subtle props (flowers)

PHOTOGRAPHY:
- Soft, flattering beauty lighting
- High-end brand quality (Sephora style)
- Sharp packaging detail
- Luxurious, aspirational mood

Generate a professional beauty product image."""
    
    # =========================================================================
    # PET SUPPLIES - Show with pets! 🐕🐱
    # =========================================================================
    
    def _pet_prompt(self, title: str, result: CategoryResult) -> str:
        # Detect pet type
        is_dog = 'dog' in title.lower()
        is_cat = 'cat' in title.lower()
        pet_type = "golden retriever dog" if is_dog else ("tabby cat" if is_cat else "cute dog")
        
        return f"""Pet product photography for e-commerce.

PRODUCT: {title}

PET: Adorable {pet_type} with the product
- Happy, friendly expression
- Natural interaction with product
- Pet and product both visible

SETTING:
- Bright, cheerful home setting
- Warm, inviting atmosphere

PHOTOGRAPHY:
- Warm lighting
- Focus on product and pet
- Happy, playful mood
- Pet store catalog quality

Generate a charming pet product image."""
    
    # =========================================================================
    # CONSUMER ELECTRONICS - Clean tech shots
    # =========================================================================
    
    def _electronics_prompt(self, title: str, result: CategoryResult) -> str:
        return f"""Professional tech product photography.

PRODUCT: {title}

PRESENTATION:
- Product only, NO human models
- Optimal angle showing design
- Show key features

BACKGROUND:
- Pure white background (#FFFFFF)
- OR sleek gradient

PHOTOGRAPHY:
- Professional studio lighting
- Apple-style clean aesthetic
- Sharp focus throughout
- Premium tech quality

Generate a professional electronics product image."""
    
    # =========================================================================
    # PHONES & ACCESSORIES
    # =========================================================================
    
    def _phone_prompt(self, title: str, result: CategoryResult) -> str:
        is_case = 'case' in title.lower()
        
        return f"""Phone accessory product photography.

PRODUCT: {title}

PRESENTATION:
- {'Phone case on smartphone display' if is_case else 'Product at optimal angle'}
- Clean, modern tech aesthetic
- NO human models

BACKGROUND:
- Pure white or minimal gradient

PHOTOGRAPHY:
- Clean, even lighting
- Sharp material detail
- Tech catalog quality

Generate a professional phone accessory image."""
    
    # =========================================================================
    # COMPUTER & OFFICE
    # =========================================================================
    
    def _computer_prompt(self, title: str, result: CategoryResult) -> str:
        return f"""Professional office product photography.

PRODUCT: {title}

PRESENTATION:
- Product at optimal angle
- Clean, professional aesthetic
- NO human models

BACKGROUND:
- White background
- OR modern desk setup

PHOTOGRAPHY:
- Professional lighting
- Sharp detail
- Business catalog quality

Generate a professional office product image."""
    
    # =========================================================================
    # HOME, GARDEN & FURNITURE - Lifestyle settings
    # =========================================================================
    
    def _home_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        
        rooms = {
            SubCategory.FURNITURE: "modern, well-lit living room",
            SubCategory.BEDDING: "cozy, inviting bedroom",
            SubCategory.KITCHEN: "bright, clean kitchen",
            SubCategory.DECOR: "stylish room setting",
            SubCategory.GARDEN: "beautiful garden setting",
        }
        
        return f"""Lifestyle home product photography.

PRODUCT: {title}

SETTING:
- {rooms.get(sub, "Appropriate room setting")}
- Aspirational interior design
- NO people in image

STYLING:
- Complementary decor elements
- Show product scale and use

PHOTOGRAPHY:
- Natural or warm lighting
- Lifestyle interior style
- Home catalog quality (IKEA style)
- Inviting, aspirational mood

Generate a lifestyle home product image."""
    
    # =========================================================================
    # HOME IMPROVEMENT - Product/demo focus
    # =========================================================================
    
    def _diy_prompt(self, title: str, result: CategoryResult) -> str:
        return f"""Home improvement product photography.

PRODUCT: {title}

PRESENTATION:
- Product clearly displayed
- Show key features
- NO human models

BACKGROUND:
- Clean white background
- OR DIY workshop context

PHOTOGRAPHY:
- Clear, even lighting
- Sharp feature detail
- Hardware catalog quality

Generate a professional hardware product image."""
    
    # =========================================================================
    # SPORTS & OUTDOORS
    # =========================================================================
    
    def _sports_prompt(self, title: str, result: CategoryResult) -> str:
        sub = result.sub_category
        gender = result.model_gender or "male"
        
        if sub == SubCategory.SPORTSWEAR:
            return f"""Sports/activewear fashion photography.

PRODUCT: {title}

MODEL: Athletic {gender} model, age 25-35
- Dynamic, energetic pose
- Athletic, fit appearance
- Showcasing the sportswear

SETTING:
- Gym or studio with sporty backdrop
- Energetic atmosphere

PHOTOGRAPHY:
- Bright, dynamic lighting
- Sharp action feel
- Athletic catalog quality

Generate a dynamic sportswear product image."""
        
        else:  # Equipment
            return f"""Sports equipment product photography.

PRODUCT: {title}

PRESENTATION:
- Product at optimal angle
- Show features and quality
- NO human models

BACKGROUND:
- Clean white
- OR sports setting

PHOTOGRAPHY:
- Clear, bright lighting
- Sharp detail
- Sports catalog quality

Generate a professional sports product image."""
    
    # =========================================================================
    # AUTOMOBILES & MOTORCYCLES
    # =========================================================================
    
    def _auto_prompt(self, title: str, result: CategoryResult) -> str:
        return f"""Automotive product photography.

PRODUCT: {title}

PRESENTATION:
- Product clearly displayed
- Show detail and quality
- NO human models

BACKGROUND:
- Clean studio background
- OR vehicle context

PHOTOGRAPHY:
- Professional lighting
- Sharp focus on features
- Automotive catalog quality

Generate a professional automotive product image."""
    
    # =========================================================================
    # GENERAL FALLBACK
    # =========================================================================
    
    def _general_prompt(self, title: str, result: CategoryResult) -> str:
        return f"""Professional product photography for e-commerce.

PRODUCT: {title}

PRESENTATION:
- Product centered on white background
- Optimal viewing angle
- NO human models

PHOTOGRAPHY:
- Clean, professional aesthetic
- Sharp detail throughout
- E-commerce catalog quality
- Accurate colors

Generate a professional product image."""


# Singleton instance
_builder = CJPromptBuilder()


def build_prompt(product: dict, category_result: CategoryResult) -> str:
    """Convenience function to build prompt"""
    return _builder.build_prompt(product, category_result)
