#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/fb.h>
#include <string.h>

#define FB_DEVICE "/dev/fb0"
#define FRAME_FILE "/var/new_frame.bin"
#define FRAME_SIZE (1024 * 600 * 4) // 2.457.600 bytes

int main() {
    int fbfd = open(FB_DEVICE, O_RDWR);
    if (fbfd == -1) {
        perror("Errore apertura /dev/fb0");
        return 1;
    }

    struct fb_var_screeninfo vinfo;
    if (ioctl(fbfd, FBIOGET_VSCREENINFO, &vinfo) == -1) {
        perror("Errore lettura VSCREENINFO");
        close(fbfd);
        return 1;
    }

    if (vinfo.yres_virtual < 1200) {
        printf("Errore: memoria virtuale insufficiente (%d)\n", vinfo.yres_virtual);
        close(fbfd);
        return 1;
    }

    size_t total_fb_size = vinfo.xres * vinfo.yres_virtual * (vinfo.bits_per_pixel / 8);
    char *fbp = (char *)mmap(0, total_fb_size, PROT_READ | PROT_WRITE, MAP_SHARED, fbfd, 0);
    
    if ((intptr_t)fbp == -1) {
        perror("Errore mmap");
        close(fbfd);
        return 1;
    }

    int current_page = 0;
    printf("Demone Sigmastar FB avviato. In attesa di %s...\n", FRAME_FILE);

    // Forza il pan a 0 iniziale per essere allineati
    vinfo.yoffset = 0;
    ioctl(fbfd, FBIOPAN_DISPLAY, &vinfo);

    while (1) {
        // Controlla se lo script wrapper ha scaricato un nuovo frame
        if (access(FRAME_FILE, F_OK) != -1) {
            FILE *img = fopen(FRAME_FILE, "rb");
            if (img) {
                int hidden_page = (current_page == 0) ? 1 : 0;
                size_t offset = hidden_page * FRAME_SIZE;

                // Copia l'immagine direttamente nella memoria video nascosta
                size_t bytes = fread(fbp + offset, 1, FRAME_SIZE, img);
                fclose(img);

                if (bytes == FRAME_SIZE) {
                    // Page Flipping Hardware Istantaneo!
                    vinfo.yoffset = hidden_page * 600;
                    if (ioctl(fbfd, FBIOPAN_DISPLAY, &vinfo) == 0) {
                        current_page = hidden_page;
                        
                        // Tentativo opzionale di sincronizzazione VSYNC
                        int dummy = 0;
                        ioctl(fbfd, FBIO_WAITFORVSYNC, &dummy); 
                    }
                }
            }
            // Cancella il frame letto in attesa del prossimo aggiornamento
            unlink(FRAME_FILE);
        }
        usleep(100000); // Check ogni 100ms, non impatta CPU
    }

    munmap(fbp, total_fb_size);
    close(fbfd);
    return 0;
}
