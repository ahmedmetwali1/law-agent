"""
🔢 Arabic Number to Text Converter
Converts numbers like 368 → "الثامنة والستون بعد الثلاثمائة"
"""


def number_to_arabic_text(num: int) -> str:
    """
    Convert number to Arabic text for Saudi legal articles.
    
    Format: [units] و[tens] بعد [hundreds]
    
    Examples:
        1 → "الأولى"
        12 → "الثانية عشرة"
        368 → "الثامنة والستون بعد الثلاثمائة"
        500 → "الخمسمائة"
    """
    
    if num < 1 or num > 999:
        return str(num)  # Fallback
    
    # ===== UNITS (1-9) - Feminine form for "المادة" =====
    units = [
        "", "الأولى", "الثانية", "الثالثة", "الرابعة", 
        "الخامسة", "السادسة", "السابعة", "الثامنة", "التاسعة"
    ]
    
    # ===== TENS (20-90) - Masculine form =====
    tens_full = {
        20: "العشرون", 30: "الثلاثون", 40: "الأربعون",
        50: "الخمسون", 60: "الستون", 70: "السبعون", 
        80: "الثمانون", 90: "التسعون"
    }
    
    # ===== 11-19 (special cases) =====
    eleven_to_nineteen = {
        11: "الحادية عشرة", 12: "الثانية عشرة", 13: "الثالثة عشرة",
        14: "الرابعة عشرة", 15: "الخامسة عشرة", 16: "السادسة عشرة",
        17: "السابعة عشرة", 18: "الثامنة عشرة", 19: "التاسعة عشرة"
    }
    
    # ===== HUNDREDS (100-900) =====
    hundreds = {
        100: "المائة", 200: "المائتان", 300: "الثلاثمائة", 
        400: "الأربعمائة", 500: "الخمسمائة", 600: "الستمائة",
        700: "السبعمائة", 800: "الثمانمائة", 900: "التسعمائة"
    }
    
    # ===== SIMPLE CASES =====
    # 1-9
    if num <=9:
        return units[num]
    
    # 10
    if num == 10:
        return "العاشرة"
    
    # 11-19
    if 11 <= num <= 19:
        return eleven_to_nineteen[num]
    
    # Exact tens (20, 30, ..., 90)
    if num in tens_full:
        return tens_full[num]
    
    # Exact hundreds (100, 200, ..., 900)
    if num in hundreds:
        return hundreds[num]
    
    # ===== COMPLEX CASES =====
    hundred_part = (num // 100) * 100
    remainder = num % 100
    ten_part = (remainder // 10) * 10
    unit_part = remainder % 10
    
    result_parts = []
    
    # === Build remainder part (units + tens) ===
    remainder_text = ""
    
    if 11 <= remainder <= 19:
        # Special case: 11-19
        remainder_text = eleven_to_nineteen[remainder]
    elif remainder == 10:
        remainder_text = "العاشرة"
    elif remainder > 0:
        # Compound: units و tens
        parts = []
        
        if unit_part > 0:
            parts.append(units[unit_part])
        
        if ten_part > 0:
            # Keep "ال" prefix for compound numbers
            ten_text = tens_full[ten_part]  # Keep as-is with "ال"
            
            if unit_part > 0:
                parts.append(" و" + ten_text)  # Space + و + tens with "ال"
            else:
                parts.append(ten_text)  # Just tens with "ال"
        
        remainder_text = "".join(parts)
    
    # === Assemble final result ===
    if hundred_part > 0:
        if remainder > 0:
            # Format: [remainder] بعد [hundreds]
            result_parts.append(remainder_text)
            result_parts.append("بعد")
            result_parts.append(hundreds[hundred_part])
        else:
            # Just the hundreds
            result_parts.append(hundreds[hundred_part])
    else:
        # Just the remainder (< 100)
        result_parts.append(remainder_text)
    
    return " ".join(result_parts)
    """
    Convert number to Arabic text for legal articles.
    
    Examples:
        1 → "الأولى"
        12 → "الثانية عشرة"
        368 → "الثامنة والستون بعد الثلاثمائة"
        500 → "الخمسمائة"
    """
    
    if num < 1 or num > 999:
        return str(num)  # Fallback for out-of-range
    
    # Units (1-9)
    units = {
        1: "الأولى", 2: "الثانية", 3: "الثالثة", 4: "الرابعة", 5: "الخامسة",
        6: "السادسة", 7: "السابعة", 8: "الثامنة", 9: "التاسعة"
    }
    
    # Tens (10-90)
    tens = {
        10: "العاشرة", 20: "العشرون", 30: "الثلاثون", 40: "الأربعون",
        50: "الخمسون", 60: "الستون", 70: "السبعون", 80: "الثمانون", 90: "التسعون"
    }
    
    # 11-19 (special cases)
    eleven_to_nineteen = {
        11: "الحادية عشرة", 12: "الثانية عشرة", 13: "الثالثة عشرة",
        14: "الرابعة عشرة", 15: "الخامسة عشرة", 16: "السادسة عشرة",
        17: "السابعة عشرة", 18: "الثامنة عشرة", 19: "التاسعة عشرة"
    }
    
    # Hundreds (100-900)
    hundreds = {
        100: "المائة", 200: "المائتان", 300: "الثلاثمائة", 400: "الأربعمائة",
        500: "الخمسمائة", 600: "الستمائة", 700: "السبعمائة", 800: "الثمانمائة", 900: "التسعمائة"
    }
    
    # Simple cases
    if num in units:
        return units[num]
    if num in eleven_to_nineteen:
        return eleven_to_nineteen[num]
    if num in tens:
        return tens[num]
    if num in hundreds:
        return hundreds[num]
    
    # Extract parts
    hundred_part = (num // 100) * 100
    remainder = num % 100
    ten_part = (remainder // 10) * 10
    unit_part = remainder % 10
    
    parts = []
    
    # Build the number: e.g., 368 = 300 + 60 + 8
    if hundred_part > 0:
        # If there are tens/units, say "بعد الـ..."
        if remainder > 0:
            parts.append(hundreds[hundred_part].replace("ال", ""))  # Remove "ال"
        else:
            parts.append(hundreds[hundred_part])
    
    # Handle 11-19 within hundreds
    if remainder in eleven_to_nineteen:
        if hundred_part > 0:
            parts.insert(0, eleven_to_nineteen[remainder])
            parts.insert(1, "بعد")
        else:
            parts.append(eleven_to_nineteen[remainder])
    elif remainder > 0:
        # Units and tens
        if unit_part > 0:
            parts.insert(0, units[unit_part])
        if ten_part > 0:
            if unit_part > 0:
                parts.insert(1, "و")
            parts.insert(1 if unit_part > 0 else 0, tens[ten_part].replace("ال", ""))
        
        if hundred_part > 0:
            parts.insert(len(parts) if unit_part or ten_part else 0, "بعد")
    
    return "".join(parts) if not hundred_part or not remainder else " ".join(parts)


# Simplified version for common patterns
def number_to_arabic_variants(num: int) -> list:
    """
    Generate common Arabic text variants for a number.
    
    Returns list of possible writings.
    """
    variants = []
    
    # Full text
    try:
        full_text = number_to_arabic_text(num)
        if full_text:
            variants.append(full_text)
    except:
        pass
    
    # Common abbreviations for hundreds
    if num >= 300:
        hundred = (num // 100) * 100
        remainder = num % 100
        
        hundreds_map = {
            300: "الثلاثمائة", 400: "الأربعمائة", 500: "الخمسمائة",
            600: "الستمائة", 700: "السبعمائة", 800: "الثمانمائة", 900: "التسعمائة"
        }
        
        if remainder < 100 and hundred in hundreds_map:
            # Try pattern: "الـ[units] بعد الـ[hundreds]"
            if remainder <= 9 and remainder > 0:
                units_simple = {
                    1: "الأولى", 2: "الثانية", 3: "الثالثة", 4: "الرابعة",
                    5: "الخامسة", 6: "السادسة", 7: "السابعة", 8: "الثامنة", 9: "التاسعة"
                }
                variants.append(f"{units_simple[remainder]} بعد {hundreds_map[hundred]}")
            
            # For 11-99
            elif remainder >= 11:
                # Just use the full text
                pass
    
    return variants


if __name__ == "__main__":
    # Test cases
    test_numbers = [1, 12, 50, 100, 368, 375, 500, 544]
    
    print("🔢 Arabic Number Converter Tests:\n")
    
    for num in test_numbers:
        text = number_to_arabic_text(num)
        variants = number_to_arabic_variants(num)
        
        print(f"{num} → {text}")
        if variants and variants[0] != text:
            print(f"      Variants: {variants}")
        print()
