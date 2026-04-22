from db import list_utilisations


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
