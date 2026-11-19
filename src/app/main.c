/**
 * @file main.c
 * @brief Firmware entry point.
 * @ingroup app
 */
#include "app.h"
#include "bsp.h"

/**
 * @brief Bring up the board, then run the application forever.
 *
 * If the board fails to initialise, the drive stays disabled and the
 * application never starts.
 *
 * @return Never returns.
 * @relation(SWR-BSP-004, SWR-APP-001, scope=function, role=Implementation)
 */
int main(void)
{
    if (!bsp_init()) {
        for (;;) {
            bsp_motor_apply((drive_cmd_t){ .enable = false, .duty = 0 });
        }
    }
    app_init();
    for (;;) {
        app_poll();
    }
}
