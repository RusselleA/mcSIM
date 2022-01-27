"""
Python script which takes command line arguments to program the DMD pattern sequence from patterns previously loaded
into DMD firmware. Firmware loading can be done using the Texas Instruments DLP6500 and DLP9000 GUI
(https://www.ti.com/tool/DLPC900REF-SW)

This file contains information about the DMD firmware patterns in the variables `channel_map` and two helper functions
`get_dmd_sequence()` and `program_dmd_seq()`. This can imported from other python files and called from there,
or this script can be run from the command line.

Run "python set_dmd_sim.py -h" on the commandline for a detailed description of command options

Information about which patterns are stored in the firmware and mapping onto different "channels" which
are associated with a particular excitation wavelength and "modes" which are associated with a certain DMD
pattern or set of DMD patterns this are stored in the variable channel_map
This is of type dict{dict{dict{np.array}}}
The top level dictionary keys are the names for each "channel"
The second level down dictionary keys are the names of the "modes" for that channel,
i.e. modes = channel_map["channel_name"].keys()
note that all channels must have a mode called 'default'
The third level dictionary specify the DMD patterns, i.e.
# modes["default"] = {"picture_indices", "bit_indices"}
So e.g. for channel="blue" to get the picture indices associated with the "sim" mode slice as follows:
channel_map["blue"]["sim"]["picture_indices"]
"""

import numpy as np
import argparse
from mcsim.expt_ctrl import dlp6500


# #######################
# define channels and modes
# #######################
channel_map = {"off": {"default": {"picture_indices": np.array([1]), "bit_indices": np.array([4])}},
               "on":  {"default": {"picture_indices": np.array([1]), "bit_indices": np.array([3])}},
               "blue": {"default": {"picture_indices": np.zeros(9, dtype=int), "bit_indices": np.arange(9, dtype=int)}},
               "red": {"default": {"picture_indices": np.zeros(9, dtype=int), "bit_indices": np.arange(9, 18, dtype=int)}},
               "green": {"default": {"picture_indices": np.array([0] * 6 + [1] * 3, dtype=int), "bit_indices": np.array(list(range(18, 24)) + list(range(3)), dtype=int)}},
               "odt": {"default": {"picture_indices": np.ones(11, dtype=int), "bit_indices": np.arange(7, 18, dtype=int)}}
            }

# add on/off modes
on_mode = channel_map["on"]["default"]
off_mode = channel_map["off"]["default"]
on_affine_mode = {"picture_indices": np.array([1]), "bit_indices": np.array([5])}
off_affine_mode = {"picture_indices": np.array([1]), "bit_indices": np.array([6])}

# add on/off/widefield/affine/sim modes for other colors
# non-inverted patterns
for m in ["red", "blue"]:
    channel_map[m].update({"off": off_mode})
    channel_map[m].update({"on": on_mode})
    channel_map[m].update({"widefield": on_mode})
    channel_map[m].update({'affine': on_affine_mode})
    channel_map[m].update({'sim': channel_map[m]["default"]})

# inverted-patterns
for m in ["green", "odt"]:
    channel_map[m].update({"off": on_mode})
    channel_map[m].update({"on": off_mode})
    channel_map[m].update({"widefield": off_mode})
    channel_map[m].update({'affine': off_affine_mode})
    channel_map[m].update({'sim': channel_map[m]["default"]})

# #######################
# firmware patterns
# #######################
ang = -45 * np.pi/180
frq = np.array([np.sin(ang), np.cos(ang)]) * 1/4 * np.sqrt(2)

rad = 5
phase = 0

# pupil info
na_mitutoyo = 0.55
dm = 7.56 # DMD mirror size
fl_mitutoyo = 4e3 # focal length of mitutoya objective
fl_olympus = 1.8e3
# magnification between DMD and Mitutoyo BFP
mag_dmd2bfp = 100 / 200 * 300 / 400 * fl_mitutoyo / fl_olympus

pupil_rad_mirrors = fl_mitutoyo * na_mitutoyo / mag_dmd2bfp / dm

# patterns
n_phis = 5
fractions = [0.5, 0.9]
phis = np.arange(n_phis) * 2*np.pi / n_phis
n_thetas = len(fractions)

xoffs = np.zeros((n_phis, n_thetas))
yoffs = np.zeros((n_phis, n_thetas))
for ii in range(n_phis):
    for jj in range(n_thetas):
        xoffs[ii, jj] = np.cos(phis[ii]) * pupil_rad_mirrors * fractions[jj]
        yoffs[ii, jj] = np.sin(phis[ii]) * pupil_rad_mirrors * fractions[jj]

xoffs = np.concatenate((np.array([0]), xoffs.ravel()))
yoffs = np.concatenate((np.array([0]), yoffs.ravel()))

firmware_pattern_map = [[{"type": "sim", "a1": np.array([-3, 11]), "a2": np.array([3, 12]), "index": 0}, # blue
                         {"type": "sim", "a1": np.array([-3, 11]), "a2": np.array([3, 12]), "index": 1},
                         {"type": "sim", "a1": np.array([-3, 11]), "a2": np.array([3, 12]), "index": 2},
                         {"type": "sim", "a1": np.array([-11, 3]), "a2": np.array([12, 3]), "index": 0},
                         {"type": "sim", "a1": np.array([-11, 3]), "a2": np.array([12, 3]), "index": 1},
                         {"type": "sim", "a1": np.array([-11, 3]), "a2": np.array([12, 3]), "index": 2},
                         {"type": "sim", "a1": np.array([-13, -12]), "a2": np.array([12, 3]), "index": 0},
                         {"type": "sim", "a1": np.array([-13, -12]), "a2": np.array([12, 3]), "index": 1},
                         {"type": "sim", "a1": np.array([-13, -12]), "a2": np.array([12, 3]), "index": 2},
                         {"type": "sim", "a1": np.array([-5, 18]), "a2": np.array([-15, 24]), "index": 0}, #red
                         {"type": "sim", "a1": np.array([-5, 18]), "a2": np.array([-15, 24]), "index": 1},
                         {"type": "sim", "a1": np.array([-5, 18]), "a2": np.array([-15, 24]), "index": 2},
                         {"type": "sim", "a1": np.array([-18, 5]), "a2": np.array([-24, 15]), "index": 0},
                         {"type": "sim", "a1": np.array([-18, 5]), "a2": np.array([-24, 15]), "index": 1},
                         {"type": "sim", "a1": np.array([-18, 5]), "a2": np.array([-24, 15]), "index": 2},
                         {"type": "sim", "a1": np.array([-11, -10]), "a2": np.array([15, 3]), "index": 0},
                         {"type": "sim", "a1": np.array([-11, -10]), "a2": np.array([15, 3]), "index": 1},
                         {"type": "sim", "a1": np.array([-11, -10]), "a2": np.array([15, 3]), "index": 2},
                         {"type": "sim", "a1": np.array([-3, 11]), "a2": np.array([3, 15]), "index": 0}, # green
                         {"type": "sim", "a1": np.array([-3, 11]), "a2": np.array([3, 15]), "index": 1},
                         {"type": "sim", "a1": np.array([-3, 11]), "a2": np.array([3, 15]), "index": 2},
                         {"type": "sim", "a1": np.array([-11, 3]), "a2": np.array([15, 3]), "index": 0},
                         {"type": "sim", "a1": np.array([-11, 3]), "a2": np.array([15, 3]), "index": 1},
                         {"type": "sim", "a1": np.array([-11, 3]), "a2": np.array([15, 3]), "index": 2}],
                        [{"type": "sim", "a1": np.array([-13, -12]), "a2": np.array([3, 12]), "index": 0},
                         {"type": "sim", "a1": np.array([-13, -12]), "a2": np.array([3, 12]), "index": 1},
                         {"type": "sim", "a1": np.array([-13, -12]), "a2": np.array([3, 12]), "index": 2},
                         {"type": "on"},
                         {"type": "off"},
                         {"type": "affine on"},
                         {"type": "affine off"}] +
                         [{"type": "odt", "xoffset": xoffs[ii], "yoffset": yoffs[ii], "angle": ang, "frequency": frq, "phase": phase, "radius": rad}
                          for ii in range(len(xoffs))]
                        ]


def validate_channel_map(cm):
    """
    check that channel_map is of the correct format
    @param cm:
    @return:
    """
    for ch in list(cm.keys()):
        modes = list(cm[ch].keys())

        if "default" not in modes:
            return False

        for m in modes:
            keys = list(cm[ch][m].keys())
            if "picture_indices" not in keys:
                return False

            pi = cm[ch][m]["picture_indices"]
            if not isinstance(pi, np.ndarray) or pi.ndim != 1:
                return False

            if "bit_indices" not in keys:
                return False

            bi = cm[ch][m]["bit_indices"]
            if not isinstance(bi, np.ndarray) or bi.ndim != 1:
                return False

    return True


def get_dmd_sequence(modes: list[str], channels: list[str], nrepeats: list[int], ndarkframes: int,
                     blank: list[bool], mode_pattern_indices=None):
    """
    Generate DMD patterns from a list of modes and channels
    @param modes:
    @param channels:
    @param nrepeats:
    @param ndarkframes:
    @param blank:
    @param mode_pattern_indices:
    @return picture_indices, bit_indices:
    """
    # check channel argument
    if isinstance(channels, str):
        channels = [channels]

    if not isinstance(channels, list):
        raise ValueError()

    nmodes = len(channels)

    # check mode argument
    if isinstance(modes, str):
        modes = [modes]

    if not isinstance(modes, list):
        raise ValueError()

    if len(modes) == 1 and nmodes > 1:
        modes = modes * nmodes

    if len(modes) != nmodes:
        raise ValueError()

    # check pattern indices argument
    if mode_pattern_indices is None:
        mode_pattern_indices = []
        for c, m in zip(channels, modes):
            npatterns = len(channel_map[c][m]["picture_indices"])
            mode_pattern_indices.append(np.arange(npatterns, dtype=int))

    if isinstance(mode_pattern_indices, int):
        mode_pattern_indices = [mode_pattern_indices]

    if not isinstance(mode_pattern_indices, list):
        raise ValueError()

    if len(mode_pattern_indices) == 1 and nmodes > 1:
        mode_pattern_indices = mode_pattern_indices * nmodes

    if len(mode_pattern_indices) != nmodes:
        raise ValueError()

    # check nrepeats correct type
    if isinstance(nrepeats, int):
        nrepeats = [nrepeats]

    if not isinstance(nrepeats, list):
        raise ValueError()

    if nrepeats is None:
        nrepeats = []
        for _ in zip(channels, modes):
            nrepeats.append(1)

    if len(nrepeats) == 1 and nmodes > 1:
        nrepeats = nrepeats * nmodes

    if len(nrepeats) != nmodes:
        raise ValueError()

    # check blank argument
    if isinstance(blank, bool):
        blank = [blank]

    if not isinstance(blank, list):
        raise ValueError()

    if len(blank) == 1 and nmodes > 1:
        blank = blank * nmodes

    if len(blank) != nmodes:
        raise ValueError()

    # processing
    pic_inds = []
    bit_inds = []
    for c, m, ind, nreps in zip(channels, modes, mode_pattern_indices, nrepeats):
        # need np.array(..., copy=True) to don't get references in arrays
        pi = np.array(np.atleast_1d(channel_map[c][m]["picture_indices"]), copy=True)
        bi = np.array(np.atleast_1d(channel_map[c][m]["bit_indices"]), copy=True)
        # select indices
        pi = pi[ind]
        bi = bi[ind]
        # repeats
        pi = np.hstack([pi] * nreps)
        bi = np.hstack([bi] * nreps)

        pic_inds.append(pi)
        bit_inds.append(bi)

    # insert dark frames
    if ndarkframes != 0:
        for ii in range(nmodes):
            ipic_off = channel_map[channels[ii]]["off"]["picture_indices"]
            ibit_off = channel_map[channels[ii]]["off"]["bit_indices"]

            pic_inds[ii] = np.concatenate((ipic_off * np.ones(ndarkframes, dtype=int), pic_inds[ii]), axis=0).astype(int)
            bit_inds[ii] = np.concatenate((ibit_off * np.ones(ndarkframes, dtype=int), bit_inds[ii]), axis=0).astype(int)

    # insert blanking frames
    for ii in range(nmodes):
        if blank[ii]:
            npatterns = len(pic_inds[ii])
            ipic_off = channel_map[channels[ii]]["off"]["picture_indices"]
            ibit_off = channel_map[channels[ii]]["off"]["bit_indices"]

            ipic_new = np.zeros((2 * npatterns), dtype=int)
            ipic_new[::2] = pic_inds[ii]
            ipic_new[1::2] = ipic_off

            ibit_new = np.zeros((2 * npatterns), dtype=int)
            ibit_new[::2] = bit_inds[ii]
            ibit_new[1::2] = ibit_off

            pic_inds[ii] = ipic_new
            bit_inds[ii] = ibit_new

    pic_inds = np.hstack(pic_inds)
    bit_inds = np.hstack(bit_inds)

    return pic_inds, bit_inds


def program_dmd_seq(dmd: dlp6500.dlp6500, modes: list[str], channels: list[str], nrepeats: list[int], ndarkframes: int,
                    blank: list[bool], mode_pattern_indices: list[int], triggered: bool, verbose=False):
    """
    convenience function for generating DMD pattern and programming DMD

    @param dmd:
    @param modes:
    @param channels:
    @param nrepeats:
    @param ndarkframes:
    @param blank:
    @param mode_pattern_indices:
    @param triggered:
    @param verbose:
    @return:
    """

    pic_inds, bit_inds = get_dmd_sequence(modes, channels, nrepeats, ndarkframes, blank, mode_pattern_indices)
    # #########################################
    # DMD commands
    # #########################################
    dmd.debug = verbose

    dmd.start_stop_sequence('stop')

    # check DMD trigger state
    delay1_us, mode_trig1 = dmd.get_trigger_in1()
    # print('trigger1 delay=%dus' % delay1_us)
    # print('trigger1 mode=%d' % mode_trig1)

    # dmd.set_trigger_in2('rising')
    mode_trig2 = dmd.get_trigger_in2()
    # print("trigger2 mode=%d" % mode_trig2)

    dmd.set_pattern_sequence(pic_inds, bit_inds, 105, 0, triggered=triggered,
                             clear_pattern_after_trigger=False, bit_depth=1, num_repeats=0, mode='pre-stored')

    if verbose:
        # print pattern info
        print("%d picture indices: " % len(pic_inds), end="")
        print(pic_inds)
        print("%d     bit indices: " % len(bit_inds), end="")
        print(bit_inds)
        print("finished programming DMD")

    return pic_inds, bit_inds

if __name__ == "__main__":

    # #######################
    # define arguments
    # #######################

    parser = argparse.ArgumentParser(description="Set DMD pattern sequence from the command line.")

    # allowed channels
    all_channels = list(channel_map.keys())
    parser.add_argument("channels", type=str, nargs="+", choices=all_channels,
                        help="supply the channels to be used in this acquisition as strings separated by spaces")

    # allowed modes
    modes = list(set([m for c in all_channels for m in list(channel_map[c].keys())]))
    modes_help = "supply the modes to be used with each channel as strings separated by spaces." \
                 "each channel supports its own list of modes.\n"
    for c in all_channels:
        modes_with_parenthesis = ["'%s'" % m for m in list(channel_map[c].keys())]
        modes_help += ("channel '%s' supports: " % c) + ", ".join(modes_with_parenthesis) + ".\n"

    parser.add_argument("-m", "--modes", type=str, nargs=1, choices=modes, default=["default"],
                        help=modes_help)

    # pattern indices
    pattern_indices_help = "Among the patterns specified in the subset specified by `channels` and `modes`," \
                           " only run these indices. For a given channel and mode, allowed indices range from 0 to npatterns - 1." \
                           "This options is most commonly used when only a single channel and mode are provided.\n"
    for c in list(channel_map.keys()):
        for m in list(channel_map[c].keys()):
            pattern_indices_help += "channel '%s` and mode '%s' npatterns = %d.\n" % (c, m, len(channel_map[c][m]["picture_indices"]))

    parser.add_argument("-i", "--pattern_indices", type=int, help=pattern_indices_help)

    parser.add_argument("-r", "--nrepeats", type=int, default=1,
                        help="number of times to repeat the patterns specificed by `channels`, `modes`, and `pattern_indices`")

    # other
    parser.add_argument("-t", "--triggered", action="store_true",
                        help="set DMD to wait for trigger before switching pattern")
    parser.add_argument("-d", "--ndarkframes", type=int, default=0,
                        help="set number of dark frames to be added before each color of SIM/widefield pattern")
    parser.add_argument("-b", "--blank", action="store_true",
                        help="set whether or not to insert OFF patterns between each SIM pattern to blank laser")
    parser.add_argument("-v", "--verbose", action="store_true", help="print more verbose DMD programming information")
    args = parser.parse_args()

    if args.verbose:
        print(args)

    # #########################################
    # load DMD and set pattern
    # #########################################
    dmd = dlp6500.dlp6500win(debug=args.verbose)

    pic_inds, bit_inds = program_dmd_seq(dmd, args.modes, args.channels, args.nrepeats, args.ndarkframes, args.blank,
                                         args.pattern_indices, args.triggered, args.verbose)

