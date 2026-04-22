from db import list_tarifs, list_utilisations


RECHARGE_HOURS = 11.0


def calculer_theorique():
    """Calculate theoretical solar panel and battery needs."""
    energie_t1_wh = 0.0
    energie_t2_wh = 0.0
    energie_t3_wh = 0.0

    utilisations = list_utilisations()

    for (
        _util_id,
        _appareil_id,
        _nom,
        puissance_w,
        _tranche_id,
        label,
        _heure_debut,
        _heure_fin,
        duree_h,
    ) in utilisations:
        energie_wh = float(puissance_w) * float(duree_h)

        if label == "T1":
            energie_t1_wh += energie_wh
        elif label == "T2":
            energie_t2_wh += energie_wh
        elif label == "T3":
            energie_t3_wh += energie_wh

    batterie_theorique_wh = energie_t3_wh
    panneau_theorique_w = (
        energie_t1_wh + energie_t2_wh + batterie_theorique_wh
    ) / RECHARGE_HOURS

    return {
        "energie_t1_wh": energie_t1_wh,
        "energie_t2_wh": energie_t2_wh,
        "energie_t3_wh": energie_t3_wh,
        "panneau_theorique_w": panneau_theorique_w,
        "batterie_theorique_wh": batterie_theorique_wh,
    }


def calculer_pratique(theorique):
    """Apply practical sizing rules to theoretical values."""
    panneau_theorique_w = float(theorique["panneau_theorique_w"])
    batterie_theorique_wh = float(theorique["batterie_theorique_wh"])
    panneau_achat_w = panneau_theorique_w / 0.4

    # Add 50% safety margin for the battery sizing.
    batterie_achat_wh = batterie_theorique_wh * 1.5

    resultat = dict(theorique)
    resultat.update(
        {
            "panneau_achat_w": panneau_achat_w,
            "batterie_achat_wh": batterie_achat_wh,
        }
    )
    return resultat


def calculer_puissance_restante(puissance_max_w):
    """
    Calculate the remaining power not used by all devices.
    
    This function calculates how much power is still available after all
    connected devices consume their required power.
    
    Workflow:
    1. Get the maximum power capacity of the solar panel (in Watts)
    2. Retrieve all devices from the database with their power consumption
    3. Sum up the total power consumed by all devices
    4. Calculate remaining power = max power - total consumed power
    5. Return the remaining power value
    
    Args:
        puissance_max_w (float): Maximum available power from solar panel (in Watts)
    
    Returns:
        dict: A dictionary containing:
            - 'puissance_max_w': The maximum available power
            - 'puissance_utilisee_w': Total power consumed by all devices
            - 'puissance_restante_w': Remaining unused power
    
    Example:
        >>> result = calculer_puissance_restante(300)
        >>> # If devices consume 200W total:
        >>> # result['puissance_restante_w'] would be 100W
    """
    
    # Step 1: Convert input to float for calculation safety
    puissance_max_w = float(puissance_max_w)
    
    # Step 2: Initialize total consumed power
    puissance_utilisee_w = 0.0
    
    # Step 3: Retrieve all device utilisations from database
    utilisations = list_utilisations()
    
    # Step 4: Sum up power consumption of all devices
    # Each utilisation contains the device's power rating
    for (
        _util_id,
        _appareil_id,
        _nom,
        puissance_w,
        _tranche_id,
        _label,
        _heure_debut,
        _heure_fin,
        _duree_h,
    ) in utilisations:
        # Add this device's power to total consumption
        puissance_utilisee_w += float(puissance_w)
    
    # Step 5: Calculate remaining power
    puissance_restante_w = puissance_max_w - puissance_utilisee_w
    
    # Step 6: Ensure remaining power is not negative (safety check)
    if puissance_restante_w < 0:
        puissance_restante_w = 0.0
    
    # Step 7: Return result dictionary with all values
    return {
        "puissance_max_w": puissance_max_w,
        "puissance_utilisee_w": puissance_utilisee_w,
        "puissance_restante_w": puissance_restante_w,
    }


def calculer_puissance_restante_pratique(puissance_max_w):
    """
    Calculate practical remaining power using hourly peak analysis.

    This function finds the peak power consumption across all operating hours,
    then calculates how much power remains available for each time period by
    subtracting the actual hourly consumption from the available peak power.

    Workflow:
    1. Build a power consumption map by analyzing each hour (0-23)
    2. For each device usage, add its power to each hour it operates
    3. Find the peak (maximum) power consumption across all hours
    4. For T1 (6-17h daytime): sum up (peak - hourly_consumption) for each hour
    5. For T2 (17-19h late afternoon): sum up (peak/2 - hourly_consumption) for each hour
       - Note: peak is halved because of reduced solar intensity at this time
    6. T3 (19-6h night) is ignored because solar panels don't produce at night
    7. Return total remaining power = reste_T1 + reste_T2

    Example calculation:
    - If peak power consumption = 500W
    - At 6-7h: consumption = 200W, remaining = 500 - 200 = 300W
    - At 7-8h: consumption = 150W, remaining = 500 - 150 = 350W
    - T1 remainder = 300 + 350 + ... = total for all T1 hours
    - For T2 at 17-18h: consumption = 100W, peak_t2 = 250W (half peak), remaining = 250 - 100 = 150W

    Args:
        puissance_max_w (float): Maximum panel power in Watts

    Returns:
        dict: Remaining power breakdown:
            - 'puissance_max_w': Input maximum power
            - 'pic_w': Peak consumption found across all hours
            - 'puissance_restante_t1_w': Remaining power for T1 (6-17h)
            - 'puissance_restante_t2_w': Remaining power for T2 (17-19h)
            - 'puissance_restante_t3_w': Always 0 (T3 is battery-driven)
            - 'puissance_restante_totale_w': Total remaining = T1 + T2
    """
    
    # Step 1: Convert input to float for calculation safety
    puissance_max_w = float(puissance_max_w)
    
    # Step 2: Initialize hourly consumption map (0-23 hours)
    # Each hour slot will accumulate power from all devices operating at that time
    consommation_par_heure = {h: 0.0 for h in range(24)}
    
    # Step 3: Retrieve all device usages from the database
    utilisations = list_utilisations()
    
    # Step 4: Build consumption profile by hour
    # For each device, add its power to every hour it operates
    for (
        _util_id,
        _appareil_id,
        _nom,
        puissance_w,
        _tranche_id,
        _label,
        heure_debut,
        heure_fin,
        _duree_h,
    ) in utilisations:
        puissance_w = float(puissance_w)
        heure_debut = int(heure_debut)
        heure_fin = int(heure_fin)
        
        # Add this device's power for each hour between debut and fin (inclusive start, exclusive end)
        for h in range(heure_debut, heure_fin):
            if 0 <= h < 24:
                consommation_par_heure[h] += puissance_w
    
    # Step 5: Find the peak power consumption across all hours
    # This represents the maximum power demand at any point during the day
    pic = max(consommation_par_heure.values()) if consommation_par_heure.values() else 0.0
    
    # Step 6: Calculate remaining power for T1 (6-17h with full peak)
    # For each hour in T1 daytime, calculate how much power is available
    puissance_restante_t1_w = 0.0
    for h in range(6, 17):  # Hours 6 through 16 (6am to 5pm)
        # Remaining power at this hour = peak available - actual consumption
        reste_heure = pic - consommation_par_heure[h]
        # Only count positive remainders (can't have negative available power)
        if reste_heure > 0:
            puissance_restante_t1_w += reste_heure
    
    # Step 7: Calculate remaining power for T2 (17-19h with half peak)
    # Solar intensity drops in late afternoon, so only half the peak is available
    puissance_restante_t2_w = 0.0
    pic_t2 = pic / 2.0  # Half the peak for late afternoon hours
    for h in range(17, 19):  # Hours 17 through 18 (5pm to 7pm)
        # Remaining power at this hour = (peak/2) available - actual consumption
        reste_heure = pic_t2 - consommation_par_heure[h]
        # Only count positive remainders
        if reste_heure > 0:
            puissance_restante_t2_w += reste_heure
    
    # Step 8: T3 (19-6h) is ignored because there is no solar production at night
    # Battery handles all power needs during these hours
    puissance_restante_t3_w = 0.0
    
    # Step 9: Calculate total remaining power
    puissance_restante_totale_w = puissance_restante_t1_w + puissance_restante_t2_w
    
    # Step 10: Return comprehensive breakdown for display and further calculations
    return {
        "puissance_max_w": puissance_max_w,
        "pic_w": pic,
        "puissance_restante_t1_w": puissance_restante_t1_w,
        "puissance_restante_t2_w": puissance_restante_t2_w,
        "puissance_restante_t3_w": puissance_restante_t3_w,
        "puissance_restante_totale_w": puissance_restante_totale_w,
    }


def calculer_puissance_reduite_wh(puissance_reduite_w):
    """
    Convert a reduced power value into energy in watt-hours.

    The goal of this helper is to take the reduced power that remains after the
    practical sizing rules and convert it into an equivalent energy value by
    multiplying it with the total number of hours used by all devices.

    Workflow:
    1. Convert the reduced power to float for a safe numeric calculation.
     2. Retrieve all usages from the database with their duration.
     3. Sum usage duration only for T1 and T2 (solar production window).
         T3 is excluded because the panel does not produce at night.
    4. Multiply the reduced power by the total duration to obtain Wh.
    5. Clamp negative values to zero so the result stays physically valid.
    6. Return a dictionary with the input power, total hours, and final Wh.

    Args:
        puissance_reduite_w (float): Reduced power value in Watts.

    Returns:
        dict: A dictionary containing:
            - 'puissance_reduite_w': Reduced power in Watts
            - 'heures_totales_utilisation_h': Total usage duration in hours
            - 'energie_reduite_wh': Converted energy in Watt-hours
    """

    # Step 1: Convert the incoming power to float before doing any math.
    puissance_reduite_w = float(puissance_reduite_w)

    # Step 2: Start with zero total usage time.
    heures_totales_utilisation_h = 0.0

    # Step 3: Load every appliance usage from the database.
    utilisations = list_utilisations()

    # Step 4: Add duration only when the usage belongs to T1 or T2.
    # T3 (night) is intentionally excluded from panel-energy conversion.
    for (
        _util_id,
        _appareil_id,
        _nom,
        _puissance_w,
        _tranche_id,
        label,
        _heure_debut,
        _heure_fin,
        duree_h,
    ) in utilisations:
        if label in ("T1", "T2"):
            heures_totales_utilisation_h += float(duree_h)

    # Step 5: Multiply reduced power by total time to get energy in Wh.
    energie_reduite_wh = puissance_reduite_w * heures_totales_utilisation_h

    # Step 6: Keep the result non-negative for consistency.
    if energie_reduite_wh < 0:
        energie_reduite_wh = 0.0

    # Step 7: Return a compact payload for the UI or future calculations.
    return {
        "puissance_reduite_w": puissance_reduite_w,
        "heures_totales_utilisation_h": heures_totales_utilisation_h,
        "energie_reduite_wh": energie_reduite_wh,
    }


def calculer_prix_tarifaire_wh(puissance_reduite_totale_w):
    """
    Calculate the cost of reduced power for the journalier and weekend tariffs.

    This function takes the total remaining practical power (in Watts) and
    multiplies it by the journalier and weekend unit tariff rates to give
    two cost scenarios.

    Workflow:
    1. Extract the reduced power value in Watts
    2. Load tariff rows from the database via list_tarifs()
    3. Normalize tariff names to identify journalier and weekend rates
    4. Multiply the reduced power by each tariff unit price
       - Cost = Power (W) × Tariff (Ar/W)
    5. Return the unit prices and total costs for both tariff scenarios

    Args:
        puissance_reduite_totale_w (float): Total remaining practical power in Watts
            (from calculer_puissance_restante_pratique["puissance_restante_totale_w"])

    Returns:
        dict: Unit prices and total costs for journalier and weekend:
            - 'prix_journalier': Unit price for journalier (Ar/W)
            - 'cout_journalier': Total cost if using journalier tariff (Ar)
            - 'prix_weekend': Unit price for weekend (Ar/W)
            - 'cout_weekend': Total cost if using weekend tariff (Ar)
    """

    # Step 1: Convert input power to float for safe calculation
    puissance_reduite_w = float(puissance_reduite_totale_w)

    # Step 2: Load all tariff rows from the database
    tarifs = list_tarifs()
    prix_par_nom = {}    # Map normalized names to prices
    prix_par_ordre = []  # Fallback: prices in row order

    # Step 3: Build price lookup maps
    for _tarif_id, _type_journee_id, nom_type_journee, prix in tarifs:
        prix_float = float(prix)
        prix_par_ordre.append(prix_float)

        # Normalize the tariff type name (e.g., "Journalier" → "JOURNALIER")
        nom_normalise = str(nom_type_journee or "").strip().upper()
        if nom_normalise:
            prix_par_nom[nom_normalise] = prix_float

    # Helper function to find a price by label or fallback to row order
    def _resolve_price(label, fallback_index):
        # Try exact match on label variations
        candidats = [label, label.upper(), label.lower()]
        for candidat in candidats:
            prix = prix_par_nom.get(str(candidat).upper())
            if prix is not None:
                return prix

        # Fallback: use row order (1st or 2nd tariff)
        if len(prix_par_ordre) >= fallback_index:
            return prix_par_ordre[fallback_index - 1]

        return 0.0

    # Step 4: Resolve prices for each tariff type
    prix_journalier = _resolve_price("journalier", 1)
    prix_weekend = _resolve_price("weekend", 2)

    # Step 5: Multiply reduced power by each tariff rate
    # Cost = Power (W) × Tariff price (Ar/W) = Total cost (Ar)
    cout_journalier = puissance_reduite_w * prix_journalier
    cout_weekend = puissance_reduite_w * prix_weekend

    # Step 6: Clamp negative costs to zero (safety check)
    if cout_journalier < 0:
        cout_journalier = 0.0
    if cout_weekend < 0:
        cout_weekend = 0.0

    # Step 7: Return tariff scenario results
    return {
        "prix_journalier": prix_journalier,
        "prix_weekend": prix_weekend,
        "cout_journalier": cout_journalier,
        "cout_weekend": cout_weekend,
    }
 