
from ansys.aedt.core import Desktop, Hfss
from ansys.aedt.core import Desktop
import math


# VARIABLES
wg_radius = 75 # inner radius.
wg_height = 500
wg_wall_thickness = 1
design_freq = 1420e6
c = 299792458.0  # Speed of light in m/s
design_lambda = c / design_freq

coax_pin_radius = 1.0 # center conductor radius mm
coax_vaccum_radius = coax_pin_radius*2.30192 # vaccum dielectric inside coax radius.
coax_gnd_radius = coax_vaccum_radius + 1.5 # 1.5 mm thick wall shield radius.
coax_pin_len = 95-10 # center conductor length mm
coax_vacc_gnd_len = 40


# return lambda_g in millimeters.
# this is used to determine probe distance to backwall.
def calc_wg_wavelength():
    c_mm = c*1e3 # speed of light in mm/s

    # 1. Calculate free-space wavelength
    lambda_0 = c_mm / design_freq
    # 2. Calculate the TE11 cutoff frequency for your specific radius (in Hz)
    # 1.8412 is the mathematical constant for the first circular waveguide mode
    f_cutoff = (1.8412 * c) / (2 * math.pi * (wg_radius / 1000.0))
    
    if design_freq > f_cutoff:
        lambda_g = lambda_0 / math.sqrt(1 - (f_cutoff / design_freq) ** 2)
        # 4. Your target back-plane distance is exactly a quarter-wave
        back_wall_dist = lambda_g / 4
        print(f"Cutoff Frequency: {f_cutoff/1e9:.3f} GHz")
        print(f"Guide Wavelength: {lambda_g:.2f} mm")
        print(f"Perfect Back Wall Distance: {back_wall_dist:.2f} mm")
        return lambda_g
    else:
        print("Error: Waveguide radius is too small! 1420 MHz is in cutoff.")
        return 0

# MORE VARIABLES.
# tweak this boi.
probe_height = calc_wg_wavelength() / 4;


# this is the main.
# Explicitly pass your installed version (Example: 2024 R1)
with Desktop(version="2025.2",student_version=True, non_graphical=False) as d:

    # # 1. Use the Desktop context manager to wrap the internal GUI process safely
    # with Desktop(new_desktop=False, close_on_exit=False) as d:
    hfss = Hfss()

    # slightly offset up by wall thickness and adjust heigh accordingly.
    hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,wg_wall_thickness],radius=wg_radius,height=wg_height-wg_wall_thickness,name="WG_cavity_sub",material="vaccum")
    hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,0],radius=wg_radius+wg_wall_thickness,height=wg_height,name="WG_walls",material="copper")

    # subtract walls from cavity to create hollow waveguide.
    hfss.modeler.subtract(
    blank_list=["WG_walls"], 
    tool_list=["WG_cavity_sub"], 
    keep_originals=False
    )

    wg_cav = hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,wg_wall_thickness],radius=wg_radius,height=wg_height-wg_wall_thickness,name="WG_cavity",material="vaccum")
    wg_cav.visible = False

    # the xoffset of the coaxial cable being connected to the exterior wall.
    # TWEAK THIS PARAMETER FOR DEPTH OF COAXIAL PENETRATION INTO WAVEGUIDE CAVITY.
    xoffset_coax = wg_radius+coax_vacc_gnd_len-1

    # offset by radius + coax_vacc_gnd_len to position the center pin inside the waveguide 
    ctrpin = hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_pin_radius,height=coax_pin_len,name="sma_probe_pin",material="copper")

    # actual vaccum material.
    hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_vaccum_radius,height=coax_vacc_gnd_len,name="sma_probe_vacc",material="vaccum")

    # vaccum sub is used to hollow out the coax between center pin and shield
    hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_vaccum_radius,height=coax_vacc_gnd_len,name="sma_probe_vacc_sub",material="vaccum")

    shieldpin = hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_gnd_radius,height=coax_vacc_gnd_len,name="sma_probe_shield",material="copper")

    # arbitrary scaling to make it thick enough to cut through wall.
    hfss.modeler.create_cylinder(orientation="X", origin=[-(wg_radius+wg_wall_thickness),0,probe_height],radius=coax_vaccum_radius,height=wg_wall_thickness*3,name="sma_wg_hole",material="vaccum") # hole for the sma center pin.

    # subtract walls from cavity to create hollow waveguide.
    hfss.modeler.subtract(
    blank_list=["WG_walls"], 
    tool_list=["sma_wg_hole"], 
    keep_originals=False
    )

    # subtract walls from cavity to create hollow waveguide.
    hfss.modeler.subtract(
    blank_list=["sma_probe_shield"], 
    tool_list=["sma_probe_vacc_sub"], 
    keep_originals=False
    )

    # hfss.assign_perfecte_to_sheets(ctrpin.name, "PerfE_Pin1")
    # hfss.assign_perfecte_to_sheets(shieldpin.name, "PerfE_Pin2")

    ## CREATE WAVEPORT AT EDGE OF COAX.
    # 1. Create a 2D Circle Sheet to act as the port surface
    # Position [X, Y, Z] should match the flat outer face of your coax dielectric
    port_sheet = hfss.modeler.create_circle(
        orientation="YZ",
        origin=[-(xoffset_coax),0,probe_height],  # Example position outside waveguide wall
        radius=coax_vaccum_radius,
        name="WavePort_Sheet"
    )


    # 2. Define the Integration Line path using exact start and stop vector lists
    # From the center pin to the inner wall of the outer shield
    int_line_start = [-(xoffset_coax),0,probe_height]       # Midpoint/Center of pin
    int_line_end   = [-(xoffset_coax),0,probe_height+coax_vaccum_radius] # Radially outward to shield edge

    # 3. Assign the Wave Port
    new_wave_port = hfss.wave_port(
        assignment=port_sheet.name,
        integration_line=[int_line_start, int_line_end],
        name="Port1",
        modes=1
    )

    # gotta do this manually!!!!!!!!!!!
    # hfss.odesign.EditDesignSettings([
    #     "NAME:Design Settings Data",
    #     "Allow Material Override:=", True,  # <-- The magic flag
    #     "Calculate Lossy Dielectrics:=", True
    # ])

    ## Setup creation
#     setup_name = "Setup1_1420MHz"
#     setup = hfss.create_setup(setupname=setup_name, SetupType="HFSSDriven")

#     # Configure convergence parameters programmatically
#     setup.props["Frequency"] = "1.42GHz"      # Target center frequency
#     setup.props["MaxPasses"] = 20             # Maximum adaptive meshing passes
#     setup.props["MaximumDeltaS"] = 0.02       # Strict convergence target for accuracy

#     # Force the solver to save the fields so you can visualize them later
#     setup.props["SaveFields"] = True


# # ==============================================================================
# # STEP 2: CREATE THE FREQUENCY SWEEP (FOR HIGH-RES S11 PLOTS)
# # ==============================================================================
# # Add a fast/interpolating frequency sweep to this specific setup
#     sweep_name = "Sweep_1_to_2_GHz"
#     sweep = hfss.create_frequency_sweep(
#         setupname=setup_name,
#         sweepname=sweep_name,
#         start_frequency="1.0GHz",
#         stop_frequency="2.0GHz",
#         num_of_freq_points=501,               # Generates a smooth, high-res curve
#         sweep_type="Interpolating"            # Keeps it lightning fast and continuous
#     )

#     print("Analysis setup and sweep configured successfully!")


    # Last step very important.
    hfss.release_desktop(close_projects=False, close_desktop=False)
    pass


