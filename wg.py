
from ansys.aedt.core import Desktop, Hfss
from ansys.aedt.core import Desktop
import math
import os

# parabolic dish measurements
# od radius of panel = 1.4m
# radius of inner mounting ring = 0.11115
# depth measured with string at deepest point = 0.1207m
# f = (1.4 - 0.11115)**2 / (16*0.1207)
# fD = f / 2.8

# VARIABLES
wg_radius = 75 # inner radius.
wg_height = 500
wg_wall_thickness = 1
design_freq = 1420e6
c = 299792458.0  # Speed of light in m/s
design_lambda = c / design_freq



coax_vacc_gnd_len = 40
coax_pin_len = coax_vacc_gnd_len + ((design_lambda*0.22)*1e3) # center conductor length mm  OBSERVED AS BEST SO FAR. @95mm radius it looks like longer is better. 104.3 IS NOW BEST BY A LOT.
print(f"CoaxPin length length: {coax_pin_len:.2f} mm")


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
# okay so tweaking this down a little furhter here provided some of the best results.
# 90.36634521569225
# so once I thickened the probe to 3mm 62.5mm probe height started to broaden the response.  I think I was hitting a "resonant mode" before, super narrow notch.
 
# 89.3
probe_height = (calc_wg_wavelength() / 4)-4 #62 #((calc_wg_wavelength() / 4)+5) - 8


start_offset = -5
count = 10
step = 0.5
sweep_param = False # turn on and off.

# I think this one created a broadband response.
# Running for probe_len 69.22335942253521
# Running for probe height 97.36634521569225

#Running for probe_len 71.22335942253521
#Running for probe height 99.36634521569225

# this is the main.
# Explicitly pass your installed version (Example: 2024 R1)
with Desktop(version="2025.2",student_version=True, non_graphical=False) as d:

    # # 1. Use the Desktop context manager to wrap the internal GUI process safely
    # with Desktop(new_desktop=False, close_on_exit=False) as d:
    hfss = Hfss()

    # CHOOSE VARIABLE TO MODIFY HERE.
    coax_pin_radius = 1.0 # center conductor radius mm

    if sweep_param:
        #Running for probe_len 86.44671884507042
        #Running for probe height 85.36634521569225
        probe_height = probe_height + start_offset
        #coax_pin_len = coax_pin_len + start_offset
        #wg_height = wg_height + start_offset
        #coax_pin_radius = coax_pin_radius + start_offset # center conductor radius mm
    else:
        count = 1



    for idx in range(0, count):


        coax_vaccum_radius = coax_pin_radius*2.30192 # vaccum dielectric inside coax radius.
        coax_gnd_radius = coax_vaccum_radius + 0.1 # 0.1 mm thick wall shield radius.

        # CHANGE PRINT STATEMENT HERE:
        #print("Running for coax_pin_radius " + str(coax_pin_radius))
        # print("Running for wg_height " + str(wg_height))
        print("Running for probe_len " + str(coax_pin_len))
        print("Running for probe height " + str(probe_height))

        # Delete all objects for fresh slate on this iteration.
        all_objects = list(hfss.modeler.object_names)

        # 2. Pass the entire list directly into the delete method
        if all_objects:
            hfss.modeler.delete(all_objects)

        #hfss.messenger.add_message("Beginning WG iteration for ")

        # slightly offset up by wall thickness and adjust heigh accordingly.
        wg_cav = hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,wg_wall_thickness],radius=wg_radius,height=wg_height,name="WG_cavity",material="vaccum")
        hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,0],radius=wg_radius+wg_wall_thickness,height=wg_height,name="WG_walls",material="copper")

        # subtract walls from cavity to create hollow waveguide.
        hfss.modeler.subtract(
        blank_list=["WG_walls"], 
        tool_list=["WG_cavity"], 
        keep_originals=True
        )

        #wg_cav = hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,wg_wall_thickness],radius=wg_radius,height=wg_height-wg_wall_thickness,name="WG_cavity",material="vaccuum")
        wg_cav.visible = False

        # the xoffset of the coaxial cable being connected to the exterior wall.
        # TWEAK THIS PARAMETER FOR DEPTH OF COAXIAL SHIELD PENETRATION INTO WAVEGUIDE CAVITY.
        xoffset_coax = wg_radius+coax_vacc_gnd_len-0.1

        # offset by radius + coax_vacc_gnd_len to position the center pin inside the waveguide 
        ctrpin = hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_pin_radius,height=coax_pin_len,name="sma_probe_pin",material="copper")

        # actual vaccum material.
        # ADJUSTED SO THAT VACCUM FULLY MEETS OTHER VACCUM INSIDE WAVE CAVITY.
        hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_vaccum_radius,height=coax_vacc_gnd_len+5,name="sma_probe_vacc",material="vaccuum")

        # vaccum sub is used to hollow out the coax between center pin and shield
        # hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_vaccum_radius,height=coax_vacc_gnd_len+5,name="sma_probe_vacc_sub",material="vaccuum")

        shieldpin = hfss.modeler.create_cylinder(orientation="X", origin=[-(xoffset_coax),0,probe_height],radius=coax_gnd_radius,height=coax_vacc_gnd_len,name="sma_probe_shield",material="copper")

        # arbitrary scaling to make it thick enough to cut through wall.
        hfss.modeler.create_cylinder(orientation="X", origin=[-(wg_radius+wg_wall_thickness),0,probe_height],radius=(coax_vaccum_radius),height=wg_wall_thickness*3,name="sma_wg_hole",material="vaccuum") # hole for the sma center pin.

        # we really need this vaccum on the end of the cylinder 
        # this will become our radiation boundary, otherwise all empty space in the simulation is treated as PEC and the waveguide will reflect back into itself
        # becoming a super High Q cavity filter.
        # overlap slightly with edge of waveguide and make radius comfortably large.
        space_vacc = hfss.modeler.create_cylinder(orientation="Z", origin=[0,0,wg_height-0.1],radius=wg_radius*5,height=wg_height,name="space_vacc",material="vaccum")
        space_vacc.visible = False
        hfss.assign_radiation_boundary_to_objects("space_vacc")

        # subtract walls from cavity to create hollow waveguide.
        hfss.modeler.subtract(
        blank_list=["WG_walls"], 
        tool_list=["sma_wg_hole"], 
        keep_originals=False
        )

        # subtract walls from cavity to create hollow waveguide.
        hfss.modeler.subtract(
        blank_list=["sma_probe_shield"], 
        tool_list=["sma_probe_vacc"], 
        keep_originals=True
        )

        hfss.modeler.unite(["sma_probe_vacc", "WG_cavity"])

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
        int_line_start = [-(xoffset_coax),0,probe_height]       # Edge of center conductor pin
        int_line_end   = [-(xoffset_coax),0,probe_height+coax_vaccum_radius] # Radially outward to shield edge

        # 3. Assign the Wave Port
        new_wave_port = hfss.wave_port(
            assignment=port_sheet.name,
            integration_line=[int_line_start, int_line_end],
            name="Port1",
            modes=1
        )
        hfss.analyze_setup("Setup1")

 

        # UPDATE VARIABLE TO MODIFY HERE.

        if sweep_param:
            probe_height = probe_height + step
            #coax_pin_len = coax_pin_len + step
            #wg_height = wg_height + step
            #coax_pin_radius = coax_pin_radius + step


        # sol_data = hfss.post.get_solution_data(
        #     expressions="dB(S(Port1,Port1))",
        #     setup_sweep_name="Setup1"
        # )
        # script_dir = "C:\\Users\\mkeat\\Documents\\"
        # report_filename = os.path.join(script_dir, f"native_s11_plot_probe_{probe_height}mm.csv")
            
        # Force PyAEDT to export the existing GUI plot to disk in one shot
        # Argument 1: Output file folder destination path
        # Argument 2: The exact literal name of the plot in your Results tree
        # Argument 3: Setup configuration name mapping
        # hfss.post.copy_report_data("dB(S(Port1,Port1))")
        # hfss.post.paste_report_data()
        # # PyAEDT hands you back two parallel arrays: all frequencies and all dB values
        # all_frequencies = sol_data.intrinsics["Freq"]  # The X-axis points (in Hz or GHz)
        # all_s11_db_values = sol_data.data_real()       # The Y-axis points (in dB)
        
        # # Track your target 1.42 GHz point just for the GUI logging update
        # # (Finds the closest frequency index to 1.42e9 in your data array)
        # target_idx = min(range(len(all_frequencies)), key=lambda i: abs(float(all_frequencies[i]) - 1.42e9))
        # s11_at_target = all_s11_db_values[target_idx]

        # # ==========================================================================
        # # FULL PLOT SAVE BLOCK: Writes the complete curve array to a unique file
        # # ==========================================================================
        # # Dynamically generate a clear, custom filename for this specific step
        # csv_filename = f"s11_plot_probe_{probe_height}mm.csv"
        
        # with open(csv_filename, 'w', newline='') as f:
        #     writer = csv.writer(f)
        #     writer.writerow(["Frequency (Hz)", "S11 (dB)"])
            
        #     # Zip the X and Y arrays together and write all 501 rows to disk instantly
        #     for freq, db_val in zip(all_frequencies, all_s11_db_values):
        #         writer.writerow([freq, db_val])

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


        # 4. Use it cleanly in the parametric sweep definition
        # param_setup = hfss.parametrics.add(
        #     variable_name="bw_var",                                         # No quotes needed here either
        #     start_value=probe_height-10,
        #     stop_value=probe_height+10,
        #     step_value=2,
        #     parametric_type="LinearStep"
        # )
        # param_setup.analyze()

    # Last step very important.
    hfss.release_desktop(close_projects=False, close_desktop=False)
    pass


