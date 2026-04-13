def validate_npi_luhn(npi: str) -> bool:
    """
    Validates a 10-digit NPI using the Luhn Algorithm.
    """
    if not npi or len(npi) != 10 or not npi.isdigit():
        return False
    
    # NPI standard uses a prefix of 80840 for the check digit calculation
    # But for the 10-digit NPI itself, we can use this simplified logic:
    npi_digits = [int(d) for d in npi]
    check_digit = npi_digits[-1]
    remaining_digits = npi_digits[:-1]
    
    # Add the 80840 prefix logic
    # 80840 -> 8+0+8+4+0 = 20. We start with 24 (8*2 + 0 + 8*2 + 4 + 0)
    total = 24 
    
    for i, digit in enumerate(reversed(remaining_digits)):
        if i % 2 == 0: # These are the even positions from the right (2nd, 4th...)
            multiplied = digit * 2
            total += multiplied if multiplied < 10 else (multiplied - 9)
        else:
            total += digit
            
    calculated_check_digit = (10 - (total % 10)) % 10
    return calculated_check_digit == check_digit