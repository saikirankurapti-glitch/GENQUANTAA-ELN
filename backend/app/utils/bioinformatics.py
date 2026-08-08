import re

def clean_sequence(sequence: str) -> str:
    """Removes whitespace and non-alphabet characters."""
    if not sequence:
        return ""
    return re.sub(r'[^a-zA-Z]', '', sequence).upper()

def calculate_gc_content(sequence: str) -> float:
    """
    Calculates the GC content of a DNA or RNA sequence.
    Returns a float representing the percentage (e.g., 45.5).
    """
    clean_seq = clean_sequence(sequence)
    if not clean_seq:
        return 0.0
    
    gc_count = clean_seq.count('G') + clean_seq.count('C')
    return round((gc_count / len(clean_seq)) * 100, 2)

def calculate_molecular_weight(sequence: str, seq_type: str = "DNA") -> float:
    """
    Estimates the molecular weight (in g/mol or Daltons) of the sequence.
    Approximations used:
    DNA: (A=313.21, T=304.2, C=289.18, G=329.21) + 79.0 (5' phosphate)
    RNA: (A=329.21, U=306.2, C=305.18, G=345.21) + 79.0
    Protein: Average amino acid = ~110 Da.
    """
    clean_seq = clean_sequence(sequence)
    if not clean_seq:
        return 0.0
        
    seq_type = seq_type.upper()
    weight = 0.0
    
    if seq_type == "PROTEIN":
        # Rough average approximation for proteins
        weight = len(clean_seq) * 110.0
    elif seq_type == "RNA":
        weights = {'A': 329.21, 'U': 306.2, 'C': 305.18, 'G': 345.21}
        for base in clean_seq:
            weight += weights.get(base, 320.0) # 320.0 as avg for unknown
        if weight > 0:
            weight += 79.0 # Terminal phosphate
    else:
        # Default to DNA
        weights = {'A': 313.21, 'T': 304.2, 'C': 289.18, 'G': 329.21}
        for base in clean_seq:
            weight += weights.get(base, 309.0) # 309.0 as avg for unknown
        if weight > 0:
            weight += 79.0
            
    return round(weight, 2)
