"""Pure Phase 2 orchestration for MOSCAP-X."""

from __future__ import annotations

from .depletion_extractor import calculate_depletion_width
from .electric_field_extractor import calculate_junction_electric_field
from .fermi_level_extractor import calculate_vp
from .work_function_extractor import (
    calculate_work_function_difference,
)
from .material_extractor import calculate_semiconductor_permittivity
from .oxide_charge_extractor import (
    calculate_effective_charge_density,
    calculate_effective_oxide_charge,
)

from .barrier_lowering_extractor import (
    calculate_image_force_barrier_lowering,
)

from .phase2_constants import (
    BOLTZMANN_CONSTANT_J_PER_K,
    ELEMENTARY_CHARGE_C,
)

from .barrier_height_extractor import (
    calculate_barrier_height,
)

from .phase2_models import (
    Phase2Inputs,
    Phase2MaterialProperties,
)

from .phase2_results import Phase2Results

from .phase2_validation import (
    validate_finite,
    validate_finite_positive,
    validate_substrate_type,
)


def calculate_phase2_summary(
    inputs: Phase2Inputs,
    materials: Phase2MaterialProperties,
) -> Phase2Results:
    """Run Phase 2 extractors in dependency order."""

    _validate_phase2_inputs(
        inputs,
        materials,
    )

    # ---------------------------------------------------------
    # 1. Semiconductor permittivity
    # ---------------------------------------------------------

    permittivity_f_per_cm = (
        calculate_semiconductor_permittivity(
            materials.relative_permittivity,
        )
    )

    # ---------------------------------------------------------
    # 2. Calculate Vp
    #
    # P-Type:
    #     Vp = (kT/q) * ln(Nv / Na)
    #
    # N-Type:
    #     Vp = (kT/q) * ln(Nc / Nd)
    #
    # doping_cm3 comes automatically from Phase 1B.
    # Nc and Nv come from user inputs.
    # ---------------------------------------------------------

    vp_v = calculate_vp(
        doping_cm3=inputs.doping_cm3,
        temperature_k=inputs.temperature_k,
        substrate_type=inputs.substrate_type,
        nc_cm3=inputs.nc_cm3,
        nv_cm3=inputs.nv_cm3,
    )

    # ---------------------------------------------------------
    # 3. Thermal voltage
    # ---------------------------------------------------------

    thermal_voltage_v = (
        BOLTZMANN_CONSTANT_J_PER_K
        * inputs.temperature_k
        / ELEMENTARY_CHARGE_C
    )

    # ---------------------------------------------------------
    # 4. Diffusion potential
    # ---------------------------------------------------------

    vd_v = (
        inputs.v0_v
        + thermal_voltage_v
    )

    # ---------------------------------------------------------
    # 5. Existing Phase 2 input values
    # ---------------------------------------------------------

    ld_cm = inputs.ld_cm
    cs_f = inputs.cs_f
    cfb_f = inputs.cfb_f

    # ---------------------------------------------------------
    # 6. Maximum depletion width
    # ---------------------------------------------------------

    wd_cm = calculate_depletion_width(
        vd_v,
        inputs.doping_cm3,
        permittivity_f_per_cm=permittivity_f_per_cm,
    )

    # ---------------------------------------------------------
    # 7. Junction electric field
    # ---------------------------------------------------------

    em_v_cm = calculate_junction_electric_field(
        inputs.v0_v,
        wd_cm,
    )

    # ---------------------------------------------------------
    # 8. Image-force barrier lowering
    # ---------------------------------------------------------

    delta_phi_b_v = (
        calculate_image_force_barrier_lowering(
            em_v_cm,
            permittivity_f_per_cm,
        )
    )

    # ---------------------------------------------------------
    # 9. Barrier height
    #
    # New formula:
    #
    # phi_b = Vd + Vp - Delta_phi_b
    # ---------------------------------------------------------

    phi_b_v = calculate_barrier_height(
        vd_v=vd_v,
        vp_v=vp_v,
        delta_phi_b_v=delta_phi_b_v,
    )

    # ---------------------------------------------------------
    # 10. Metal-semiconductor work-function difference
    #
    # P-Type:
    #     Phi_ms = Phi_m - (X + Eg - Vp)
    #
    # N-Type:
    #     Phi_ms = Phi_m - (X + Vp)
    # ---------------------------------------------------------

    work_function = (
        calculate_work_function_difference(
            phi_m_ev=inputs.phi_m_ev,
            electron_affinity_ev=(
                materials.electron_affinity_ev
            ),
            bandgap_ev=materials.bandgap_ev,
            vp_v=vp_v,
            substrate_type=inputs.substrate_type,
        )
    )

    # ---------------------------------------------------------
    # 11. Effective oxide charge
    # ---------------------------------------------------------

    qeff_c_cm2 = calculate_effective_oxide_charge(
        inputs.cox_f,
        inputs.vfb_v,
        work_function.phi_ms,
        inputs.area_cm2,
    )

    # ---------------------------------------------------------
    # 12. Effective charge density
    # ---------------------------------------------------------

    neff_cm2 = calculate_effective_charge_density(
        qeff_c_cm2,
    )

    # ---------------------------------------------------------
    # 13. Return Phase 2 results
    # ---------------------------------------------------------

    return Phase2Results(
        cox_f=inputs.cox_f,
        vfb_v=inputs.vfb_v,
        vd_v=vd_v,
        vp_v=vp_v,
        ld_cm=ld_cm,
        wd_cm=wd_cm,
        em_v_cm=em_v_cm,
        delta_phi_b_v=delta_phi_b_v,
        cs_f=cs_f,
        phi_b_v=phi_b_v,
        cfb_f=cfb_f,
        phi_ms_v=work_function.phi_ms,
        qeff_c_cm2=qeff_c_cm2,
        neff_cm2=neff_cm2,
    )


def calculate_phase2_results(
    inputs: Phase2Inputs,
    materials: Phase2MaterialProperties,
) -> Phase2Results:
    """Compatibility alias for the typed Phase 2 orchestrator."""

    return calculate_phase2_summary(
        inputs,
        materials,
    )


def _validate_phase2_inputs(
    inputs: Phase2Inputs,
    materials: Phase2MaterialProperties,
) -> None:
    """Validate all Phase 2 inputs and material properties."""

    validate_finite_positive(
        inputs.area_cm2,
        "Device area",
    )

    validate_finite_positive(
        inputs.temperature_k,
        "Temperature",
    )

    validate_finite_positive(
        inputs.doping_cm3,
        "Doping concentration",
    )

    validate_substrate_type(
        inputs.substrate_type,
    )

    validate_finite_positive(
        inputs.cox_f,
        "Oxide capacitance",
    )

    validate_finite(
        inputs.vfb_v,
        "Flat-band voltage",
    )

    validate_finite(
        inputs.phi_m_ev,
        "Metal work function",
    )

    validate_finite_positive(
        inputs.nc_cm3,
        "Conduction-band density of states",
    )

    validate_finite_positive(
        inputs.nv_cm3,
        "Valence-band density of states",
    )

    validate_finite_positive(
        inputs.ld_cm,
        "Debye length",
    )

    validate_finite_positive(
        inputs.cs_f,
        "Semiconductor capacitance",
    )

    validate_finite_positive(
        inputs.cfb_f,
        "Flat-band capacitance",
    )

    validate_finite_positive(
        materials.intrinsic_concentration_cm3,
        "Intrinsic concentration",
    )

    validate_finite_positive(
        materials.bandgap_ev,
        "Bandgap",
    )

    validate_finite_positive(
        materials.electron_affinity_ev,
        "Electron affinity",
    )

    validate_finite_positive(
        materials.relative_permittivity,
        "Relative permittivity",
    )


Phase2Summary = Phase2Results