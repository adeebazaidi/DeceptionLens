import re
from typing import Dict, List, Any
from .normalization import normalize_date, normalize_name, normalize_location, normalize_money

def extract_role(source_text: str, roles_dict: Dict[str, List[str]]) -> str:
    """
    Given a source text and a dictionary mapping role names to lists of keywords,
    returns the role name if a keyword is found in the source text.
    Returns 'unknown' if no keyword matches.
    """
    if not source_text:
        return "unknown"
    
    text_lower = source_text.lower()
    for role, keywords in roles_dict.items():
        for kw in keywords:
            if kw in text_lower:
                return role
    return "unknown"

def check_consistency(entities: Dict[str, List[Dict[str, Any]]], case_info: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Analyzes extracted entities for internal inconsistencies.
    Uses source context to determine semantic fields and only compares values within the same field.
    """
    issues = []
    if case_info is None:
        case_info = {}

    # 1. Date Inconsistencies
    date_roles = {
        "incident_date": ["incident date", "occurrence date", "date of incident", "incident occurred"],
        "report_date": ["report date", "filing date", "submission date", "report filed"],
        "dob": ["birth date", "date of birth", "dob"],
        "issue_date": ["issue date", "appointment date", "registration date"],
        "expiry_date": ["expiry date"]
    }
    
    dates = entities.get("dates", [])
    if dates:
        grouped_dates = {}
        for d in dates:
            role = extract_role(d.get("source_text", ""), date_roles)
            if role == "unknown":
                continue # Don't compare unknown roles
                
            norm = normalize_date(d["value"])
            if not norm or len(norm) < 4: continue
            
            d["normalized"] = norm
            
            if role not in grouped_dates:
                grouped_dates[role] = {}
            if norm not in grouped_dates[role]:
                grouped_dates[role][norm] = []
            grouped_dates[role][norm].append(d)
            
        for role, norm_groups in grouped_dates.items():
            if len(norm_groups) > 1:
                evidence = [d for group in norm_groups.values() for d in group]
                issues.append({
                    "type": "DATE_INCONSISTENCY",
                    "title": "Potential date inconsistency",
                    "field": role,
                    "reason": f"Two different dates appear to refer to the {role.replace('_', ' ')}.",
                    "evidence": evidence
                })

    # 2. Location Inconsistencies
    location_roles = {
        "incident_location": ["incident location", "place of incident", "occurrence location", "crime scene"],
        "police_station": ["police station", "jurisdiction"],
        "residence": ["address", "residence"]
    }
    
    locations = entities.get("locations", [])
    if locations:
        grouped_locs = {}
        for l in locations:
            role = extract_role(l.get("source_text", ""), location_roles)
            if role == "unknown":
                continue
                
            norm = normalize_location(l["value"])
            if not norm or len(norm) < 3: continue
            l["normalized"] = norm
            
            if role not in grouped_locs:
                grouped_locs[role] = {}
                
            # Simple deduplication
            words = set(norm.split())
            matched_key = None
            for key in grouped_locs[role].keys():
                key_words = set(key.split())
                if words.intersection(key_words):
                    matched_key = key
                    break
            
            if matched_key:
                grouped_locs[role][matched_key].append(l)
            else:
                grouped_locs[role][norm] = [l]
                
        for role, norm_groups in grouped_locs.items():
            if len(norm_groups) > 1:
                evidence = [l for group in norm_groups.values() for l in group]
                issues.append({
                    "type": "LOCATION_INCONSISTENCY",
                    "title": "Potential location inconsistency",
                    "field": role,
                    "reason": f"Multiple distinct locations refer to the {role.replace('_', ' ')}.",
                    "evidence": evidence
                })

    # 3. Person/Name Inconsistencies
    person_roles = {
        "accused": ["accused", "defendant", "respondent"],
        "victim": ["victim"],
        "witness": ["witness"],
        "complainant": ["complainant", "applicant"],
        "officer": ["officer"]
    }
    
    persons = entities.get("persons", [])
    if persons:
        grouped_persons = {}
        for p in persons:
            role = extract_role(p.get("source_text", ""), person_roles)
            if role == "unknown":
                continue
                
            norm = normalize_name(p["value"])
            p["normalized"] = norm
            
            if role not in grouped_persons:
                grouped_persons[role] = {}
            if norm not in grouped_persons[role]:
                grouped_persons[role][norm] = []
            grouped_persons[role][norm].append(p)
            
        for role, norm_groups in grouped_persons.items():
            if len(norm_groups) > 1:
                evidence = [p for group in norm_groups.values() for p in group]
                issues.append({
                    "type": "NAME_INCONSISTENCY",
                    "title": "Potential name inconsistency",
                    "field": role,
                    "reason": f"Multiple distinct names are associated with the role of {role.replace('_', ' ')}.",
                    "evidence": evidence
                })
                
    # 4. Amount Inconsistencies
    money_roles = {
        "total_loss": ["total amount", "total loss"],
        "compensation": ["compensation", "damages"],
        "fine": ["fine", "penalty"],
        "salary": ["salary"],
        "payable": ["amount payable", "amount received", "transaction amount"]
    }
    
    money = entities.get("money", [])
    if money:
        grouped_money = {}
        for m in money:
            role = extract_role(m.get("source_text", ""), money_roles)
            if role == "unknown":
                continue
                
            norm = normalize_money(m["value"])
            if norm is None: continue
            m["normalized"] = str(norm)
            
            if role not in grouped_money:
                grouped_money[role] = {}
            if norm not in grouped_money[role]:
                grouped_money[role][norm] = []
            grouped_money[role][norm].append(m)
            
        for role, norm_groups in grouped_money.items():
            if len(norm_groups) > 1:
                evidence = [m for group in norm_groups.values() for m in group]
                issues.append({
                    "type": "AMOUNT_INCONSISTENCY",
                    "title": "Potential amount inconsistency",
                    "field": role,
                    "reason": f"Different monetary values appear to refer to the {role.replace('_', ' ')}.",
                    "evidence": evidence
                })

    # 5. Case Number Inconsistencies
    case_numbers = case_info.get("case_numbers", [])
    if case_numbers:
        grouped_cases = {}
        for c in case_numbers:
            # We don't have predefined roles for case numbers usually, but we can differentiate Case No vs FIR No
            text_lower = c.get("source_text", "").lower()
            role = "unknown"
            if "fir" in text_lower:
                role = "fir_number"
            elif "case" in text_lower:
                role = "case_number"
                
            if role == "unknown":
                continue
                
            norm = re.sub(r'[\s]+', '', c["value"].lower())
            c["normalized"] = norm
            
            if role not in grouped_cases:
                grouped_cases[role] = {}
            if norm not in grouped_cases[role]:
                grouped_cases[role][norm] = []
            grouped_cases[role][norm].append(c)
            
        for role, norm_groups in grouped_cases.items():
            if len(norm_groups) > 1:
                evidence = [c for group in norm_groups.values() for c in group]
                issues.append({
                    "type": "CASE_ID_INCONSISTENCY",
                    "title": "Potential case identifier inconsistency",
                    "field": role,
                    "reason": f"Multiple different identifiers found for {role.replace('_', ' ')}.",
                    "evidence": evidence
                })

    if not issues:
        status = "No inconsistency detected"
    elif len(issues) == 1:
        status = "Potential inconsistency"
    else:
        status = "Multiple potential inconsistencies"
        
    return {
        "status": status,
        "issues": issues
    }
