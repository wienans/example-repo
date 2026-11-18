/**
 * @file bsp.c
 * @brief Motor board implementation on top of the HAL.
 * @ingroup bsp
 */
#include "bsp.h"

#include "board_config.h"
#include "bsp_convert.h"
#include "hal_adc.h"
#include "hal_encoder.h"
#include "hal_gpio.h"
#include "hal_pwm.h"
#include "hal_tick.h"

/** @brief Encoder reading of the previous bsp_motor_sample() call. */
static uint16_t s_encoder_previous;

/**
 * @brief Initialise all peripherals in order and stop at the first failure.
 * @relation(SWR-BSP-004, scope=function)
 */
bool bsp_init(void)
{
    const bool ok = hal_tick_init() == HAL_OK &&
                    hal_gpio_init(BOARD_PIN_MOTOR_ENABLE, HAL_GPIO_OUTPUT) == HAL_OK &&
                    hal_gpio_init(BOARD_PIN_MOTOR_DIR, HAL_GPIO_OUTPUT) == HAL_OK &&
                    hal_gpio_init(BOARD_PIN_BUTTON_START, HAL_GPIO_INPUT) == HAL_OK &&
                    hal_gpio_init(BOARD_PIN_BUTTON_STOP, HAL_GPIO_INPUT) == HAL_OK &&
                    hal_pwm_init(BOARD_PWM_CH_MOTOR, BOARD_PWM_FREQ_HZ) == HAL_OK &&
                    hal_encoder_init(BOARD_ENCODER_MOTOR) == HAL_OK &&
                    hal_adc_init(BOARD_ADC_CH_MOTOR_CURRENT) == HAL_OK;
    if (!ok) {
        return false;
    }
    bsp_motor_apply((drive_cmd_t){ .enable = false, .duty = 0 });
    s_encoder_previous = hal_encoder_count(BOARD_ENCODER_MOTOR);
    return true;
}

/**
 * @brief Read the HAL time base.
 * @relation(SWR-APP-001, scope=function)
 */
uint32_t bsp_millis(void)
{
    return hal_tick_ms();
}

/**
 * @brief Encoder delta to rpm and ADC raw to mA.
 * @relation(SWR-BSP-001, SWR-BSP-002, scope=function)
 */
motor_sample_t bsp_motor_sample(void)
{
    const uint16_t count = hal_encoder_count(BOARD_ENCODER_MOTOR);
    const int32_t delta = bsp_encoder_delta(s_encoder_previous, count);
    s_encoder_previous = count;
    return (motor_sample_t){
        .speed_rpm = bsp_counts_to_rpm(delta),
        .current_ma = bsp_adc_to_ma(hal_adc_read(BOARD_ADC_CH_MOTOR_CURRENT)),
    };
}

/**
 * @brief Map a signed drive command onto direction, PWM and enable.
 * @relation(SWR-BSP-003, scope=function)
 */
void bsp_motor_apply(drive_cmd_t cmd)
{
    const int32_t magnitude = cmd.duty < 0 ? -(int32_t)cmd.duty : (int32_t)cmd.duty;
    hal_gpio_write(BOARD_PIN_MOTOR_DIR, cmd.duty >= 0);
    hal_pwm_set_duty(BOARD_PWM_CH_MOTOR, (uint16_t)magnitude);
    hal_gpio_write(BOARD_PIN_MOTOR_ENABLE, cmd.enable);
}

/**
 * @brief Translate button pin levels into pressed flags.
 * @relation(SWR-APP-002, scope=function)
 */
bsp_buttons_t bsp_read_buttons(void)
{
    return (bsp_buttons_t){
        .start_pressed = hal_gpio_read(BOARD_PIN_BUTTON_START) == BOARD_BUTTON_PRESSED_LEVEL,
        .stop_pressed = hal_gpio_read(BOARD_PIN_BUTTON_STOP) == BOARD_BUTTON_PRESSED_LEVEL,
    };
}
