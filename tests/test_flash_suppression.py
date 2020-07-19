# -*- coding: utf-8 -*-
#
#         PySceneDetect: Python-Based Video Scene Detector
#   ---------------------------------------------------------------
#     [  Site: http://www.bcastell.com/projects/PySceneDetect/   ]
#     [  Github: https://github.com/Breakthrough/PySceneDetect/  ]
#     [  Documentation: http://pyscenedetect.readthedocs.org/    ]
#
# Copyright (C) 2014-2020 Brandon Castellano <http://www.bcastell.com>.
#
# PySceneDetect is licensed under the BSD 3-Clause License; see the included
# LICENSE file, or visit one of the following pages for details:
#  - https://github.com/Breakthrough/PySceneDetect/
#  - http://www.bcastell.com/projects/PySceneDetect/
#
# This software uses Numpy, OpenCV, click, tqdm, simpletable, and pytest.
# See the included LICENSE files or one of the above URLs for more information.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

""" PySceneDetect Flash Suppression Tests

This file includes unit tests for the scenedetect.content_detector module, mainly
focused on flicker/flash reduction.
"""

# Standard project pylint disables for unit tests using pytest.
# pylint: disable=no-self-use, protected-access, multiple-statements, invalid-name
# pylint: disable=redefined-outer-name


from __future__ import print_function

from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.frame_timecode import FrameTimecode
from scenedetect.detectors import ContentDetector


EXPECTED_NUM_SCENES_WITH_SUPPRESSION = 3
EXPECTED_NUM_SCENES_WITHOUT_SUPPRESSION = 6
FLICKER_SUPPRESSION_RATE = 2
FLICKER_RATE = 100


class FlashingVideoManager(VideoManager):
    """ Custom video manager for testing, outputs a "flash" every N frames. """

    def __init__(self, video_files, flicker_rate=FLICKER_RATE):
        # type: (List[str], Optional[int])
        super(FlashingVideoManager, self).__init__(video_files)
        self._flicker_rate = flicker_rate
        self._num_read = 0

    def read(self):
        read_frame, frame = super(FlashingVideoManager, self).read()

        if read_frame:
            self._num_read += 1
            if (self._num_read % self._flicker_rate) == 0:
                frame.fill(0xFF)

        return read_frame, frame

    def retrieve(self):
        retrieved, frame = super(FlashingVideoManager, self).retrieve()

        if retrieved and (self._num_read % self._flicker_rate) == 0:
            frame.fill(0xFF)

        return retrieved, frame


def detect_and_return_num_scenes(video_file, flicker_frames):
    """ Runs ContentDetector with the specified amount of flash suppression,
    and the remaining as all default parameters.

    Arguments:
        video_file (str): Path to video file.
        flicker_frames (int): flicker_frames parameter to pass to ContentDetector.

    Returns:
        int: Number of detected scenes, or -1 on failure.
    """
    vm = FlashingVideoManager([video_file])
    sm = SceneManager()
    sm.add_detector(ContentDetector(flicker_frames=flicker_frames))

    try:
        base_timecode = vm.get_base_timecode()
        video_fps = vm.get_framerate()
        start_time = FrameTimecode('00:00:05', video_fps)
        end_time = FrameTimecode('00:00:15', video_fps)

        assert end_time.get_frames() > start_time.get_frames()

        vm.set_duration(start_time=start_time, end_time=end_time)
        vm.set_downscale_factor()

        vm.start()
        num_frames = sm.detect_scenes(frame_source=vm)

        assert num_frames == (1 + end_time.get_frames() - start_time.get_frames())

        scene_list = sm.get_scene_list(base_timecode)
        assert scene_list
        return len(scene_list)

    # pylint: disable=bare-except
    except:
        return -1

    finally:
        vm.release()


def test_no_flash_suppression(test_video_file):
    """ Test ContentDetector without any flash suppression.

    Used to validate constants at the top of this file.
    """
    assert detect_and_return_num_scenes(
        test_video_file, 0) == EXPECTED_NUM_SCENES_WITHOUT_SUPPRESSION



def test_flash_suppression(test_video_file):
    """ Test ContentDetector flicker suppression capability (flicker_frames argument). """

    assert detect_and_return_num_scenes(
        test_video_file, FLICKER_SUPPRESSION_RATE) == EXPECTED_NUM_SCENES_WITH_SUPPRESSION

