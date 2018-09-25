import uzlib
import uhashlib
import ustruct
import ubinascii
import gc

class ShittyTar(object):
    def __init__(self, content):
        self.content = content
        self.index = 0
        self.header_fmt = ">HL32s"

    def verify(self):
        # Just make sure we can iterate through all files in the archive
        # without any exceptions due to decompression, buffer underrun, etc.
        for _ in self:
            pass
        return True
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.index >= len(self.content):
            # Reset the index so we can iterate over this archive repeatedly.
            self.index = 0
            raise StopIteration()
    
        gc.collect()
        
        header_size = ustruct.calcsize(self.header_fmt)
        header = self.content[self.index:self.index + header_size]
        self.index += header_size
        (name_len, content_len, sha256) = ustruct.unpack(self.header_fmt, header)
        name = self.content[self.index:self.index + name_len]
        name = name.decode("ascii")
        self.index += name_len
        #print("Header: %s (%d bytes, sha256=%s)" % (name, content_len, ubinascii.hexlify(sha256)))
        content = self.content[self.index:self.index + content_len]
        self.index += content_len
        our_sha256 = uhashlib.sha256(content).digest()
        #print("Content: %d bytes (sha256=%s)" % (len(content), ubinascii.hexlify(our_sha256)))
        decompressed_content = uzlib.decompress(content)
        #print("Content decompressed to %d bytes" % len(decompressed_content))
        
        gc.collect()

        return name, decompressed_content

    
