import time
import random
import keyboard
import ctypes
import win32api
import win32gui
import win32process
import psutil

from apcmini.apcmini import ApcMini


from win32con import VK_MEDIA_PLAY_PAUSE, VK_VOLUME_DOWN, VK_VOLUME_UP, VK_MEDIA_NEXT_TRACK, VK_MEDIA_PREV_TRACK, KEYEVENTF_EXTENDEDKEY
from collections import deque
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
from ctypes import POINTER, cast, HRESULT, POINTER, c_float, c_uint32
from ctypes.wintypes import UINT
from comtypes import CLSCTX_ALL, COMMETHOD, GUID, IUnknown



class IAudioMeterInformation(IUnknown):
    _iid_ = GUID('{c02216f6-8c67-4b5b-9d00-d008e73e0064}')
    _methods_ = (
        COMMETHOD([], HRESULT, 'GetPeakValue',
				(['out'], 
				POINTER(c_float), 
				'pfPeak')
		),		
        COMMETHOD([], HRESULT, 'GetMeteringChannelCount',
				(['out'], 
				POINTER(UINT), 
				'pnChannelCount')
		),		
        COMMETHOD([], HRESULT, 'GetChannelsPeakValues',
				(['in'], 
				c_uint32, 
				'u32ChannelCount'),
				(['out'],
				(POINTER(c_float) * 8),
				'afPeakValues')
	    ),
	)




def get_active_window_pid():
	hwnd = win32gui.GetForegroundWindow()
	tid, current_pid = win32process.GetWindowThreadProcessId(hwnd)
	return current_pid
def get_active_window_name():
	hwnd = win32gui.GetForegroundWindow()
	tid, current_pid = win32process.GetWindowThreadProcessId(hwnd)
	try:
		return psutil.Process(current_pid).name() 
	except Exception:
		return ""

if __name__ == "__main__":
	print("APC mini Audio Control by Secret (https://secco.dev/)")
	while 1:
		try:
			apc = ApcMini(None, "APC MINI 1")
		except Exception as e:
			print(f"\nCouldnt connect to APC mini. ({e})\ntrying again in 5 seconds...")
			time.sleep(5)
		else:
			break
	presses_buttons = []
	peaks = deque([0]*8)
	main_speaker = AudioUtilities.GetSpeakers()
	main_speaker_interface = main_speaker.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
	main_volume = cast(main_speaker_interface, POINTER(IAudioEndpointVolume))
	
	main_peaks_interface = main_speaker.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
	main_peaks = cast(main_peaks_interface, POINTER(IAudioMeterInformation))


	activitylasttime = windowlasstime = peakslasttime = time.time()
	
	bypass = False
	slidererror = [False]*8
	currentmatrix = [0]*64
	lastname = ""
	sspeed = 0.1
	mode = False
	def reset_sessions():
		global sessions, sessions_meter
		sessions = [sess for i, sess in enumerate(AudioUtilities.GetAllSessions()) if sess.Process and i<8] #limit to 8 processes
		print(" | ".join([session.Process.name() if session.Process else "System" for session in sessions]))
		sessions_meter = [session._ctl.QueryInterface(IAudioMeterInformation) for session in sessions]
	reset_sessions()
	while True:
		time.sleep(0.001) #prevent the loop from going too fast and using up a bunch of cpu. (20% -> 0.1% cpu usage)
		currenttime = time.time()
		for msg in apc.pending_inputs():
			try:
				if msg.type == "control_change":
					#if msg.value <= 2:
					#	msg.value = 0
					print(f"{msg.control} {msg.value/127}, {msg.value}                                 ", end="\r")
					if msg.control == 56:
						#print((msg.value/127)*-96)
						main_volume.SetMasterVolumeLevelScalar(msg.value/127, None)
					elif 48 <= msg.control <= 56:
						try:
							sessions[msg.control-48].SimpleAudioVolume.SetMasterVolume(msg.value/127, None)
						except IndexError:
							if not slidererror[msg.control-48] or bypass:
								slidererror[msg.control-48] = True
								apc.set(msg.control-48, "red")
				elif msg.type == "note_on":
					if msg.note == 98:
						apc.reset()
						peaks = deque([0]*8)
						presses_buttons = []
						lastname = 0
						currentmatrix = [0]*64
					elif msg.note == 64:
						win32api.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_EXTENDEDKEY, 0)
					elif msg.note == 65:
						win32api.keybd_event(VK_VOLUME_DOWN, 0, KEYEVENTF_EXTENDEDKEY, 0)
					elif msg.note == 66:
						win32api.keybd_event(VK_MEDIA_PREV_TRACK, 0, KEYEVENTF_EXTENDEDKEY, 0)
					elif msg.note == 67:
						win32api.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_EXTENDEDKEY, 0)
					elif msg.note == 68:
						win32api.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_EXTENDEDKEY, 0)
					#elif msg.note == 70:
					#	bypass = not bypass
					#	if bypass:
					#		apc.set(70, "red")
					#	else:
					#		apc.set(70, 0)
					elif msg.note == 85:
						keyboard.press_and_release('m')
					elif msg.note == 86:
						mode = not mode
						apc.reset()
						if mode:
							apc.set(86, 1)
						else:
							apc.set(86, 0)
					elif msg.note == 87:
						sspeed -= 0.01
						print(sspeed)
					elif msg.note == 88:
						sspeed += 0.01
						print(sspeed)
					elif msg.note == 71:
						oldlen = len(sessions)
						reset_sessions()
						newlen = len(sessions)
						for i in range(oldlen, newlen): #turn on if we have more
							apc.set(64+i, 1)
						for i in range(newlen, oldlen): #turn off if we have less
							apc.set(64+i, 0)
						print(" | ".join([session.Process.name() if session.Process else "System" for session in sessions]))
						lastname = 0
					elif msg.note < 64 and currentmatrix[msg.note]:
						apc.set(msg.note, 0)
					elif msg.note in presses_buttons:
						apc.set(msg.note, 0)
						presses_buttons.remove(msg.note)
					else:
						apc.set(msg.note, 1)
						presses_buttons.append(msg.note)		
			except Exception:
				print("\n:( looks like the script crashed. Heres some info:")
				print(msg)
				print(f"{msg.type=} ▒ {msg.note=} ▒ {msg.control=}")
				raise
		if (currenttime-windowlasstime) >= 1:
			slidererror = [False]*8
			windowlasstime = currenttime
			currentname = get_active_window_name()
			if lastname != currentname:
				lastname = currentname
				for i, session in enumerate(sessions):
					if session.Process:
						if currentname == session.Process.name():
							apc.set(64+i, "red_blinking")
						else:
							apc.set(64+i, "red")
		if (currenttime - peakslasttime) >= sspeed:
			peakslasttime = currenttime
			#channel_count = main_peaks.GetMeteringChannelCount()
			#channels = main_peaks.GetChannelsPeakValues(channel_count)
			#channel_peaks = ctypes.cast(channels, ctypes.POINTER(ctypes.c_float))
			if mode:
				for i, meter in enumerate(sessions_meter):
					peak = max(min((meter.GetPeakValue()*12)-1, 8), 0)
					for j in range(8):
						if peak <= j:
							newval = 0
						else:
							if j == 7:
								newval = 3
							else:
								newval = 5
						if currentmatrix[8*j+i] != newval or bypass:
							apc.set(8*j+i, newval)
							currentmatrix[8*j+i] = newval
			else:
				#print(peaks)
				peaks.rotate(1)
				peaks[0] = max(min((main_peaks.GetPeakValue()*12)-1, 8), 0)
				for i, v in enumerate(peaks):
					for j in range(8):
						if v <= j:
							newval = 0
						else:
							#print(8*j+1)
							if j == 7:
								newval = 3
							else:
								newval = 5
						if currentmatrix[8*j+i] != newval or bypass:
							apc.set(8*j+i, newval)
							currentmatrix[8*j+i] = newval
		if (currenttime - activitylasttime) >= 0.2:
			activitylasttime = currenttime
			print(f"{apc.activity*5:3}/s |{apc.activity:3}", "▒"*int(apc.activity/2), " "*(100-apc.activity))
			apc.activity = 0

