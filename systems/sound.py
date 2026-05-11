import pygame
import os

"""Audio manager wrapping pygame.mixer for Pacman Arcade sound effects."""

class SoundManager:
    """Loads WAV files and plays them on dedicated mixer channels.
    Channel assignments:
        0 - waka      : looping movement sound; starts when Pacman moves,
                        stops when stationary.
        1 - power     : one-shot played when a power pellet is collected.
        2 - eat_ghost : one-shot played each time a frightened ghost is eaten.
        3 - die       : one-shot played on Pacman death; halts all other audio.
    """
    def __init__(self):
        
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)
        self.sounds = {}
        self.channels = {
            'waka'          :     pygame.mixer.Channel(0),
            'power'         :     pygame.mixer.Channel(1),
            'eat_ghost'     :     pygame.mixer.Channel(2),
            'die'           :     pygame.mixer.Channel(3) 
        }
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sound_dir = os.path.join(base_dir, 'assets', 'sounds')

        for name in ('waka', 'power', 'eat_ghost', 'die'):
            try:
                file_path = os.path.join(sound_dir, f'{name}.wav')
                self.sounds[name] = pygame.mixer.Sound(file_path)
            except FileNotFoundError:
                print(f"Warning: Không tìm thấy âm thanh {file_path}")
    
    def play(self, name):
        """Play the named sound effect according to its channel policy.
        Policies:
            'waka'      – starts looping only if the channel is not already busy.
            'die'       – calls pygame.mixer.stop() then plays once on channel 3.
            everything else – stops the channel first, then plays once.
        Does nothing silently if name is not in self.sounds (file was missing).
        """
        if name not in self.sounds:
            return
        channel = self.channels[name]
        if name == 'waka':
            if not channel.get_busy():
                channel.play(self.sounds[name], loops = -1)
        elif name == 'die':
            pygame.mixer.stop()
            channel.play(self.sounds[name])
        else:
            channel.stop()
            channel.play(self.sounds[name])
    
    def stop(self, name):
        """Stop the channel associated with name immediately.
        Does nothing if name is not a recognised channel key.
        """
        if name in self.channels:
            self.channels[name].stop()
