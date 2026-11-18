/**
 * @file board_config.h
 * @brief Pin map, peripheral channels and sensor scaling of the motor board.
 * @ingroup bsp
 */
#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

#include "hal_adc.h"
#include "hal_encoder.h"
#include "hal_gpio.h"
#include "hal_pwm.h"

/** @brief H-bridge direction input; high drives forward. */
#define BOARD_PIN_MOTOR_DIR ((hal_gpio_pin_t)0)
/** @brief H-bridge enable input; low lets the motor coast. */
#define BOARD_PIN_MOTOR_ENABLE ((hal_gpio_pin_t)1)
/** @brief Start push button. */
#define BOARD_PIN_BUTTON_START ((hal_gpio_pin_t)2)
/** @brief Stop push button. */
#define BOARD_PIN_BUTTON_STOP ((hal_gpio_pin_t)3)
/** @brief Input level of a pressed button (buttons pull the line low). */
#define BOARD_BUTTON_PRESSED_LEVEL false

/** @brief PWM channel feeding the H-bridge. */
#define BOARD_PWM_CH_MOTOR ((hal_pwm_channel_t)0)
/** @brief PWM carrier frequency, above the audible range. */
#define BOARD_PWM_FREQ_HZ 20000u

/** @brief Quadrature counter on the motor shaft. */
#define BOARD_ENCODER_MOTOR ((hal_encoder_id_t)0)
/** @brief Quadrature counts per shaft revolution (4096 lines x 4 edges). */
#define BOARD_ENCODER_CPR 16384

/** @brief ADC channel of the bidirectional current-sense amplifier. */
#define BOARD_ADC_CH_MOTOR_CURRENT ((hal_adc_channel_t)0)
/** @brief ADC count at zero current (mid-scale of a 12-bit converter). */
#define BOARD_ADC_ZERO_COUNT 2048
/**
 * @brief Current per ADC count as NUM/DEN mA.
 *
 * 3300 mV reference over 4096 counts with a 100 mV/A sensor gives
 * 3300 * 1000 / (4096 * 100) = 33000/4096 mA per count.
 */
#define BOARD_ADC_MA_PER_COUNT_NUM 33000
/** @brief Denominator of the ADC current scale. */
#define BOARD_ADC_MA_PER_COUNT_DEN 4096

#endif
