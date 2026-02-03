"""
Complete Category System for CJ Dropshipping Image Enhancement.
Handles ALL 14 CJ product categories with optimized detection.

Category Detection Strategy:
- Women's Clothing → Female model
- Men's Clothing → Male model
- Toys, Kids & Babies → Child model (clothing) / Product only (toys)
- Jewelry & Watches → Model (worn) / Display (rings, watches)
- Bags & Shoes → Model holding/wearing
- Health, Beauty & Hair → Product focus
- Pet Supplies → Pet model!
- Consumer Electronics → Product only
- Phones & Accessories → Product only
- Computer & Office → Product only
- Home, Garden & Furniture → Lifestyle setting
- Home Improvement → Product/Demo
- Sports & Outdoors → Active model (sportswear) / Product (equipment)
- Automobiles & Motorcycles → Product focus
"""

import re
from enum import Enum
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass


class CJCategory(Enum):
    """All CJ Dropshipping categories"""
    WOMENS_CLOTHING = "womens_clothing"
    MENS_CLOTHING = "mens_clothing"
    TOYS_KIDS_BABIES = "toys_kids_babies"
    JEWELRY_WATCHES = "jewelry_watches"
    BAGS_SHOES = "bags_shoes"
    HEALTH_BEAUTY_HAIR = "health_beauty_hair"
    PET_SUPPLIES = "pet_supplies"
    CONSUMER_ELECTRONICS = "consumer_electronics"
    PHONES_ACCESSORIES = "phones_accessories"
    COMPUTER_OFFICE = "computer_office"
    HOME_GARDEN_FURNITURE = "home_garden_furniture"
    HOME_IMPROVEMENT = "home_improvement"
    SPORTS_OUTDOORS = "sports_outdoors"
    AUTOMOBILES_MOTORCYCLES = "automobiles_motorcycles"
    GENERAL = "general"


class SubCategory(Enum):
    """Sub-categories for more specific prompts"""
    # Women's Clothing
    WOMENS_DRESS = "womens_dress"
    WOMENS_TOP = "womens_top"
    WOMENS_BOTTOM = "womens_bottom"
    WOMENS_OUTERWEAR = "womens_outerwear"
    WOMENS_SWIMWEAR = "womens_swimwear"
    WOMENS_ACTIVEWEAR = "womens_activewear"
    
    # Men's Clothing
    MENS_SHIRT = "mens_shirt"
    MENS_PANTS = "mens_pants"
    MENS_SUIT = "mens_suit"
    MENS_OUTERWEAR = "mens_outerwear"
    MENS_ACTIVEWEAR = "mens_activewear"
    
    # Kids
    BABY_CLOTHING = "baby_clothing"
    KIDS_CLOTHING = "kids_clothing"
    TOYS = "toys"
    BABY_GEAR = "baby_gear"
    
    # Jewelry
    NECKLACE = "necklace"
    EARRINGS = "earrings"
    BRACELET = "bracelet"
    RING = "ring"
    WATCH = "watch"
    
    # Bags & Shoes
    HANDBAG = "handbag"
    BACKPACK = "backpack"
    WALLET = "wallet"
    WOMENS_SHOES = "womens_shoes"
    MENS_SHOES = "mens_shoes"
    
    # Beauty
    MAKEUP = "makeup"
    SKINCARE = "skincare"
    HAIRCARE = "haircare"
    
    # Pet
    PET_CLOTHING = "pet_clothing"
    PET_TOYS = "pet_toys"
    PET_ACCESSORIES = "pet_accessories"
    
    # Electronics
    HEADPHONES = "headphones"
    SPEAKERS = "speakers"
    CAMERA = "camera"
    GAMING = "gaming"
    
    # Computer
    LAPTOP = "laptop"
    KEYBOARD_MOUSE = "keyboard_mouse"
    
    # Home
    FURNITURE = "furniture"
    BEDDING = "bedding"
    KITCHEN = "kitchen"
    DECOR = "decor"
    GARDEN = "garden"
    
    # Sports
    FITNESS_EQUIPMENT = "fitness_equipment"
    SPORTSWEAR = "sportswear"
    OUTDOOR_GEAR = "outdoor_gear"
    
    # Auto
    CAR_ACCESSORIES = "car_accessories"
    MOTORCYCLE_GEAR = "motorcycle_gear"
    
    # General
    GENERAL = "general"


@dataclass
class CategoryResult:
    """Result of category detection"""
    main_category: CJCategory
    sub_category: SubCategory
    needs_human_model: bool
    needs_pet_model: bool
    model_gender: Optional[str]  # "female", "male", "child", None
    model_age_range: Optional[str]
    confidence: float
    
    def __str__(self) -> str:
        model = "No model"
        if self.needs_human_model:
            model = f"{self.model_gender} model ({self.model_age_range})"
        elif self.needs_pet_model:
            model = "Pet model"
        return f"{self.main_category.value}/{self.sub_category.value} [{model}]"


class CJCategoryDetector:
    """
    Detects CJ category from product information.
    Maps to appropriate prompt strategy.
    """
    
    # =========================================================================
    # CATEGORY PATTERNS
    # =========================================================================
    
    PATTERNS: Dict[CJCategory, Dict] = {
        # Women's Clothing
        CJCategory.WOMENS_CLOTHING: {
            "keywords": [
                r"\b(women'?s?|woman'?s?|ladies'?|female)\b",
                r"\b(dress|gown|skirt|blouse|bikini|tankini)\b",
                r"\b(leggings|tights|cardigan|tunic|romper|jumpsuit)\b",
                r"\b(maternity|nursing|plus.size)\b",
            ],
            "sub_patterns": {
                SubCategory.WOMENS_DRESS: r"\b(dress|gown|maxi|midi|mini.dress)\b",
                SubCategory.WOMENS_TOP: r"\b(top|blouse|shirt|sweater|cardigan|tee|tank|t-shirt)\b",
                SubCategory.WOMENS_BOTTOM: r"\b(pants|jeans|skirt|shorts|leggings|trousers|flare)\b",
                SubCategory.WOMENS_OUTERWEAR: r"\b(jacket|coat|blazer|vest|hoodie|parka|fleece)\b",
                SubCategory.WOMENS_SWIMWEAR: r"\b(bikini|swimsuit|swimwear|tankini|one.piece)\b",
                SubCategory.WOMENS_ACTIVEWEAR: r"\b(yoga|athletic|gym|sports.bra|workout|activewear)\b",
            }
        },
        
        # Men's Clothing
        CJCategory.MENS_CLOTHING: {
            "keywords": [
                r"\b(men'?s?|man'?s?|male|gentleman'?s?)\b",
                r"\b(blazer|suit|tuxedo|boxer|briefs)\b",
                r"\b(polo|henley|chino)\b",
            ],
            "sub_patterns": {
                SubCategory.MENS_SHIRT: r"\b(shirt|tee|t-shirt|polo|henley|top)\b",
                SubCategory.MENS_PANTS: r"\b(pants|jeans|shorts|trousers|chinos|joggers)\b",
                SubCategory.MENS_SUIT: r"\b(suit|blazer|tuxedo|formal|tie)\b",
                SubCategory.MENS_OUTERWEAR: r"\b(jacket|coat|hoodie|vest|sweater)\b",
                SubCategory.MENS_ACTIVEWEAR: r"\b(athletic|gym|sports|workout|track)\b",
            }
        },
        
        # Toys, Kids & Babies
        CJCategory.TOYS_KIDS_BABIES: {
            "keywords": [
                r"\b(kid'?s?|child|children|baby|infant|toddler)\b",
                r"\b(boy'?s?|girl'?s?|teen|youth|junior)\b",
                r"\b(toy|game|puzzle|doll|action.figure|dinosaur)\b",
                r"\b(newborn|onesie|stroller|crib)\b",
            ],
            "sub_patterns": {
                SubCategory.BABY_CLOTHING: r"\b(baby|infant|newborn|onesie|romper).*(cloth|wear|outfit)\b",
                SubCategory.KIDS_CLOTHING: r"\b(kid|child|boy|girl|teen).*(cloth|wear|dress|shirt)\b",
                SubCategory.TOYS: r"\b(toy|game|puzzle|doll|figure|lego|plush|dinosaur|baseball.cap)\b",
                SubCategory.BABY_GEAR: r"\b(stroller|crib|car.seat|high.chair|bottle|pacifier)\b",
            }
        },
        
        # Jewelry & Watches
        CJCategory.JEWELRY_WATCHES: {
            "keywords": [
                r"\b(jewelry|jewellery|necklace|earring|bracelet|ring)\b",
                r"\b(watch|timepiece|wristwatch)\b",
                r"\b(gold|silver|diamond|gemstone|pearl)\b",
            ],
            "sub_patterns": {
                SubCategory.NECKLACE: r"\b(necklace|pendant|choker|chain)\b",
                SubCategory.EARRINGS: r"\b(earring|ear.stud|hoop|dangle)\b",
                SubCategory.BRACELET: r"\b(bracelet|bangle|cuff|wristband|anklet)\b",
                SubCategory.RING: r"\b(ring|band|signet)\b",
                SubCategory.WATCH: r"\b(watch|timepiece|smartwatch)\b",
            }
        },
        
        # Bags & Shoes
        CJCategory.BAGS_SHOES: {
            "keywords": [
                r"\b(bag|handbag|purse|tote|backpack|wallet|crossbody)\b",
                r"\b(shoe|sneaker|boot|heel|sandal|slipper)\b",
                r"\b(belt|scarf|hat|cap|gloves|sunglasses)\b",
            ],
            "sub_patterns": {
                SubCategory.HANDBAG: r"\b(handbag|purse|tote|clutch|shoulder.bag|crossbody|evening)\b",
                SubCategory.BACKPACK: r"\b(backpack|messenger|satchel|duffel)\b",
                SubCategory.WALLET: r"\b(wallet|card.holder|coin.purse|money.clip)\b",
                SubCategory.WOMENS_SHOES: r"\b(heel|pump|flat|sandal|wedge|sneaker)\b",
                SubCategory.MENS_SHOES: r"\b(oxford|loafer|derby|brogue|sneaker)\b",
            }
        },
        
        # Health, Beauty & Hair
        CJCategory.HEALTH_BEAUTY_HAIR: {
            "keywords": [
                r"\b(makeup|cosmetic|beauty|skincare|haircare)\b",
                r"\b(lipstick|mascara|foundation|serum|cream)\b",
                r"\b(shampoo|conditioner|hair.dryer|straightener)\b",
                r"\b(perfume|fragrance|cologne)\b",
            ],
            "sub_patterns": {
                SubCategory.MAKEUP: r"\b(makeup|lipstick|mascara|foundation|eyeshadow|blush)\b",
                SubCategory.SKINCARE: r"\b(skincare|moisturizer|serum|cream|cleanser|toner)\b",
                SubCategory.HAIRCARE: r"\b(shampoo|conditioner|hair.dryer|straightener|curler)\b",
            }
        },
        
        # Pet Supplies
        CJCategory.PET_SUPPLIES: {
            "keywords": [
                r"\b(pet|dog|cat|puppy|kitten|animal)\b",
                r"\b(collar|leash|pet.bed|pet.toy|pet.bowl)\b",
                r"\b(aquarium|fish|bird|hamster|rabbit)\b",
            ],
            "sub_patterns": {
                SubCategory.PET_CLOTHING: r"\b(pet|dog|cat).*(cloth|costume|sweater|jacket)\b",
                SubCategory.PET_TOYS: r"\b(pet|dog|cat).*(toy|ball|chew|scratch)\b",
                SubCategory.PET_ACCESSORIES: r"\b(collar|leash|harness|carrier|tag|bowl)\b",
            }
        },
        
        # Consumer Electronics
        CJCategory.CONSUMER_ELECTRONICS: {
            "keywords": [
                r"\b(electronic|gadget|device|tech)\b",
                r"\b(headphone|earphone|speaker|bluetooth)\b",
                r"\b(camera|drone|gopro|action.cam)\b",
                r"\b(tv|television|projector|streaming)\b",
            ],
            "sub_patterns": {
                SubCategory.HEADPHONES: r"\b(headphone|earphone|earbud|airpod)\b",
                SubCategory.SPEAKERS: r"\b(speaker|soundbar|bluetooth.speaker)\b",
                SubCategory.CAMERA: r"\b(camera|lens|tripod|drone|gopro)\b",
                SubCategory.GAMING: r"\b(gaming|console|controller|playstation|xbox|nintendo)\b",
            }
        },
        
        # Phones & Accessories
        CJCategory.PHONES_ACCESSORIES: {
            "keywords": [
                r"\b(phone|smartphone|iphone|android|mobile)\b",
                r"\b(phone.case|screen.protector|charger|cable)\b",
                r"\b(power.bank|adapter|wireless.charger)\b",
            ],
            "sub_patterns": {}
        },
        
        # Computer & Office
        CJCategory.COMPUTER_OFFICE: {
            "keywords": [
                r"\b(computer|laptop|pc|macbook|notebook)\b",
                r"\b(keyboard|mouse|monitor|webcam)\b",
                r"\b(printer|scanner|office|desk.accessory)\b",
            ],
            "sub_patterns": {
                SubCategory.LAPTOP: r"\b(laptop|notebook|macbook|chromebook)\b",
                SubCategory.KEYBOARD_MOUSE: r"\b(keyboard|mouse|mousepad|wrist.rest)\b",
            }
        },
        
        # Home, Garden & Furniture
        CJCategory.HOME_GARDEN_FURNITURE: {
            "keywords": [
                r"\b(furniture|sofa|chair|table|bed|mattress)\b",
                r"\b(home.decor|curtain|rug|pillow|blanket)\b",
                r"\b(kitchen|cookware|utensil|appliance)\b",
                r"\b(garden|plant|outdoor|patio)\b",
            ],
            "sub_patterns": {
                SubCategory.FURNITURE: r"\b(sofa|couch|chair|table|desk|shelf|cabinet)\b",
                SubCategory.BEDDING: r"\b(bed|mattress|pillow|blanket|sheet|duvet)\b",
                SubCategory.KITCHEN: r"\b(kitchen|cookware|pot|pan|knife|utensil)\b",
                SubCategory.DECOR: r"\b(decor|vase|frame|mirror|clock|art)\b",
                SubCategory.GARDEN: r"\b(garden|plant|pot|outdoor|patio|lawn)\b",
            }
        },
        
        # Home Improvement
        CJCategory.HOME_IMPROVEMENT: {
            "keywords": [
                r"\b(tool|hardware|drill|saw|hammer)\b",
                r"\b(plumbing|electrical|paint|wallpaper)\b",
                r"\b(storage|organization|shelf|hook)\b",
                r"\b(lock|security|door|window)\b",
            ],
            "sub_patterns": {}
        },
        
        # Sports & Outdoors
        CJCategory.SPORTS_OUTDOORS: {
            "keywords": [
                r"\b(sport|fitness|gym|yoga|exercise)\b",
                r"\b(outdoor|camping|hiking|fishing|hunting)\b",
                r"\b(bike|cycling|running|swimming)\b",
                r"\b(basketball|football|soccer|tennis|golf)\b",
            ],
            "sub_patterns": {
                SubCategory.FITNESS_EQUIPMENT: r"\b(dumbbell|weight|yoga.mat|resistance|treadmill)\b",
                SubCategory.SPORTSWEAR: r"\b(jersey|shorts|leggings|sports.bra|athletic)\b",
                SubCategory.OUTDOOR_GEAR: r"\b(tent|sleeping.bag|backpack|hiking)\b",
            }
        },
        
        # Automobiles & Motorcycles
        CJCategory.AUTOMOBILES_MOTORCYCLES: {
            "keywords": [
                r"\b(car|auto|vehicle|automobile)\b",
                r"\b(motorcycle|motorbike|scooter|bike)\b",
                r"\b(car.accessory|seat.cover|dash.cam)\b",
                r"\b(helmet|gloves|riding.gear)\b",
            ],
            "sub_patterns": {
                SubCategory.CAR_ACCESSORIES: r"\b(car|auto).*(accessory|cover|mat|organizer)\b",
                SubCategory.MOTORCYCLE_GEAR: r"\b(motorcycle|helmet|riding|biker)\b",
            }
        },
    }
    
    # =========================================================================
    # DETECTION LOGIC
    # =========================================================================
    
    def detect(self, product: dict) -> CategoryResult:
        """Detect category from product information"""
        
        title = product.get('title', '') or ''
        description = (product.get('description', '') or '')[:500]
        product_type = product.get('productType', '') or ''
        tags = ' '.join(product.get('tags', []) or [])
        
        text = f"{title} {description} {product_type} {tags}".lower()
        
        # Score each category
        scores = {}
        for category, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns.get("keywords", []):
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            scores[category] = score
        
        # Get best match
        best_category = max(scores, key=scores.get)
        
        # If no match, default to general
        if scores[best_category] == 0:
            return self._create_general_result(product)
        
        # Detect sub-category
        sub_category = self._detect_subcategory(text, best_category)
        
        # Determine model requirements
        return self._create_result(best_category, sub_category, text)
    
    def _detect_subcategory(self, text: str, category: CJCategory) -> SubCategory:
        """Detect specific sub-category"""
        if category not in self.PATTERNS:
            return SubCategory.GENERAL
        
        sub_patterns = self.PATTERNS[category].get("sub_patterns", {})
        
        for sub_cat, pattern in sub_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return sub_cat
        
        return SubCategory.GENERAL
    
    def _create_result(self, category: CJCategory, sub_category: SubCategory, text: str) -> CategoryResult:
        """Create result with model requirements"""
        
        # Default values
        needs_human = False
        needs_pet = False
        gender = None
        age_range = None
        
        # Category-specific logic
        if category == CJCategory.WOMENS_CLOTHING:
            needs_human = True
            gender = "female"
            age_range = "25-35"
            
        elif category == CJCategory.MENS_CLOTHING:
            needs_human = True
            gender = "male"
            age_range = "28-40"
            
        elif category == CJCategory.TOYS_KIDS_BABIES:
            # Toys don't need models, only kids clothing
            if sub_category in [SubCategory.BABY_CLOTHING, SubCategory.KIDS_CLOTHING]:
                needs_human = True
                gender = "child"
                age_range = "4-10"
            
        elif category == CJCategory.JEWELRY_WATCHES:
            # Necklaces, earrings, bracelets look better ON a model
            if sub_category in [SubCategory.NECKLACE, SubCategory.EARRINGS, SubCategory.BRACELET]:
                needs_human = True
                gender = "female"
                age_range = "25-35"
            
        elif category == CJCategory.BAGS_SHOES:
            needs_human = True
            # Detect gender from text
            if re.search(r"\b(women|female|lady|girl)\b", text, re.IGNORECASE):
                gender = "female"
            elif re.search(r"\b(men|male|guy|boy)\b", text, re.IGNORECASE):
                gender = "male"
            else:
                gender = "female"  # Default for bags
            age_range = "25-35"
            
        elif category == CJCategory.PET_SUPPLIES:
            # Pet products should show pets!
            if sub_category in [SubCategory.PET_CLOTHING, SubCategory.PET_TOYS, SubCategory.PET_ACCESSORIES]:
                needs_pet = True
            
        elif category == CJCategory.SPORTS_OUTDOORS:
            if sub_category == SubCategory.SPORTSWEAR:
                needs_human = True
                if re.search(r"\b(women|female)\b", text, re.IGNORECASE):
                    gender = "female"
                elif re.search(r"\b(men|male)\b", text, re.IGNORECASE):
                    gender = "male"
                else:
                    gender = "male"
                age_range = "25-35"
        
        return CategoryResult(
            main_category=category,
            sub_category=sub_category,
            needs_human_model=needs_human,
            needs_pet_model=needs_pet,
            model_gender=gender,
            model_age_range=age_range,
            confidence=0.85
        )
    
    def _create_general_result(self, product: dict) -> CategoryResult:
        """Create general/fallback result"""
        return CategoryResult(
            main_category=CJCategory.GENERAL,
            sub_category=SubCategory.GENERAL,
            needs_human_model=False,
            needs_pet_model=False,
            model_gender=None,
            model_age_range=None,
            confidence=0.3
        )


# Singleton instance
_detector = CJCategoryDetector()


def detect_category(product: dict) -> CategoryResult:
    """Convenience function to detect category"""
    return _detector.detect(product)
