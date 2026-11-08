import math
import re
import json

def grade_filter(model_output_str):
    """Grades Task 1: Sallen-Key LPF calculations"""
    try:
        # Extract JSON from response
        match = re.search(r'\{.*\}', model_output_str, re.DOTALL)
        if not match:
            return 0.0
        data = json.loads(match.group(0))
        
        R1, R2 = float(data['R1']), float(data['R2'])
        C1, C2 = float(data['C1']), float(data['C2'])
        
        # Calculate actual cutoff frequency based on chosen values
        fc_calculated = 1.0 / (2 * math.pi * math.sqrt(R1 * R2 * C1 * C2))
        
        # Target: 1000 Hz +/- 50 Hz (950 Hz to 1050 Hz)
        if 950.0 <= fc_calculated <= 1050.0:
            return 1.0
        return 0.0
    except Exception:
        return 0.0

def grade_verilog(model_output_str):
    """Grades Task 2: Verilog clock divider logic checks"""
    try:
        # Clean block formatting
        code = model_output_str.replace('```verilog', '').replace('```', '')
        
        # Basic static syntax check requirements
        checks = [
            "module clk_divider" in code,
            "input wire clk" in code or "input clk" in code,
            "input wire rst" in code or "input rst" in code,
            "output reg clk_out" in code or "output clk_out" in code,
            "always @" in code and "posedge clk" in code,
            "posedge rst" in code or "negedge rst" in code or "if (rst)" in code
        ]
        
        score = sum(1 for c in checks if c) / len(checks)
        return 1.0 if score == 1.0 else round(score, 2)
    except Exception:
        return 0.0

def grade_stm32_usart(model_output_str):
    """Grades Task 3: STM32 Baud Rate Register math"""
    # APB1 = 42MHz, Baud = 115200
    # USARTDIV = 42,000,000 / (16 * 115200) = 22.7864583
    # Mantissa = 22 (0x16)
    # Fraction = round(0.7864583 * 16) = 13 (0xD)
    # BRR = (22 << 4) | 13 = 352 | 13 = 365 = 0x16D
    EXPECTED_BRR = "0x16d"
    
    try:
        match = re.search(r'\{.*\}', model_output_str, re.DOTALL)
        if not match:
            return 0.0
        data = json.loads(match.group(0))
        
        brr_val = str(data.get('BRR_hex', '')).strip().lower()
        if brr_val == EXPECTED_BRR:
            return 1.0
        return 0.0
    except Exception:
        return 0.0