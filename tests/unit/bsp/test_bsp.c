#include <stdbool.h>
#include <stdint.h>

#include "unity.h"
#include "board_config.h"
#include "bsp.h"
#include "bsp_convert.h"
#include "mock_hal_adc.h"
#include "mock_hal_encoder.h"
#include "mock_hal_gpio.h"
#include "mock_hal_pwm.h"
#include "mock_hal_tick.h"

#define PINS 8

/* A fake board behind the HAL mocks: init calls share one counter so a
 * test can make the n-th initialisation fail, and outputs are latched per
 * pin so assertions read the resulting hardware state. */
static int init_calls;
static int fail_init_at;
static bool out_level[PINS];
static bool in_level[PINS];
static uint16_t pwm_duty;
static uint16_t encoder_count;
static uint16_t adc_raw;

static hal_status_t next_init(void)
{
    return init_calls++ == fail_init_at ? HAL_ERROR : HAL_OK;
}

static hal_status_t fake_tick_init(int n) { (void)n; return next_init(); }
static hal_status_t fake_gpio_init(hal_gpio_pin_t pin, hal_gpio_dir_t dir, int n) { (void)pin; (void)dir; (void)n; return next_init(); }
static hal_status_t fake_pwm_init(hal_pwm_channel_t ch, uint32_t hz, int n) { (void)ch; (void)hz; (void)n; return next_init(); }
static hal_status_t fake_encoder_init(hal_encoder_id_t id, int n) { (void)id; (void)n; return next_init(); }
static hal_status_t fake_adc_init(hal_adc_channel_t ch, int n) { (void)ch; (void)n; return next_init(); }
static void fake_gpio_write(hal_gpio_pin_t pin, bool level, int n) { (void)n; out_level[pin] = level; }
static bool fake_gpio_read(hal_gpio_pin_t pin, int n) { (void)n; return in_level[pin]; }
static void fake_pwm_set_duty(hal_pwm_channel_t ch, uint16_t duty, int n) { (void)n; if (ch == BOARD_PWM_CH_MOTOR) { pwm_duty = duty; } }
static uint16_t fake_encoder_count(hal_encoder_id_t id, int n) { (void)id; (void)n; return encoder_count; }
static uint16_t fake_adc_read(hal_adc_channel_t ch, int n) { (void)ch; (void)n; return adc_raw; }

void setUp(void)
{
    init_calls = 0;
    fail_init_at = -1;
    for (int i = 0; i < PINS; i++) {
        out_level[i] = true;
        in_level[i] = !BOARD_BUTTON_PRESSED_LEVEL;
    }
    pwm_duty = 999;
    encoder_count = 0;
    adc_raw = BOARD_ADC_ZERO_COUNT;
    hal_tick_init_Stub(fake_tick_init);
    hal_gpio_init_Stub(fake_gpio_init);
    hal_pwm_init_Stub(fake_pwm_init);
    hal_encoder_init_Stub(fake_encoder_init);
    hal_adc_init_Stub(fake_adc_init);
    hal_gpio_write_Stub(fake_gpio_write);
    hal_gpio_read_Stub(fake_gpio_read);
    hal_pwm_set_duty_Stub(fake_pwm_set_duty);
    hal_encoder_count_Stub(fake_encoder_count);
    hal_adc_read_Stub(fake_adc_read);
}

void tearDown(void) {}

/**
 * @brief Successful init returns true and leaves the bridge disabled at 0 % duty.
 * @relation(SWR-BSP-004, scope=function, role=Test)
 */
void test_init_success_leaves_drive_disabled(void)
{
    TEST_ASSERT_TRUE(bsp_init());
    TEST_ASSERT_FALSE(out_level[BOARD_PIN_MOTOR_ENABLE]);
    TEST_ASSERT_EQUAL_UINT16(0, pwm_duty);
}

/**
 * @brief A failure of any one HAL initialisation makes bsp_init return false.
 * @relation(SWR-BSP-004, scope=function, role=Test)
 */
void test_init_fails_when_any_hal_init_fails(void)
{
    TEST_ASSERT_TRUE(bsp_init());
    const int total = init_calls;
    TEST_ASSERT_GREATER_THAN_INT(0, total);

    for (int failing = 0; failing < total; failing++) {
        setUp();
        fail_init_at = failing;
        TEST_ASSERT_FALSE_MESSAGE(bsp_init(), "a failing HAL init was not reported");
    }
}

/**
 * @brief Time comes from the HAL tick.
 * @relation(SWR-APP-001, scope=function, role=Test)
 */
void test_millis_reads_hal_tick(void)
{
    hal_tick_ms_ExpectAndReturn(123456u);
    TEST_ASSERT_EQUAL_UINT32(123456u, bsp_millis());
}

/**
 * @brief Speed is the counts since the previous sample, across a counter wrap.
 * @relation(SWR-BSP-001, scope=function, role=Test)
 */
void test_sample_speed_from_encoder_delta_across_wrap(void)
{
    TEST_ASSERT_EQUAL_INT(1, BSP_SAMPLE_PERIOD_MS);
    encoder_count = 65000;
    TEST_ASSERT_TRUE(bsp_init());

    encoder_count = (uint16_t)(65000u + 4096u);
    TEST_ASSERT_EQUAL_INT32(15000, bsp_motor_sample().speed_rpm);

    encoder_count = (uint16_t)(encoder_count + 273u);
    TEST_ASSERT_EQUAL_INT32(999, bsp_motor_sample().speed_rpm);

    TEST_ASSERT_EQUAL_INT32(0, bsp_motor_sample().speed_rpm);
}

/**
 * @brief Reverse rotation across the zero count gives negative speed.
 * @relation(SWR-BSP-001, scope=function, role=Test)
 */
void test_sample_reverse_speed_across_wrap(void)
{
    encoder_count = 100;
    TEST_ASSERT_TRUE(bsp_init());

    encoder_count = (uint16_t)(100u + 65536u - 4096u);
    TEST_ASSERT_EQUAL_INT32(-15000, bsp_motor_sample().speed_rpm);
}

/**
 * @brief Current comes from the current-sense ADC in mA.
 * @relation(SWR-BSP-002, scope=function, role=Test)
 */
void test_sample_current_from_adc(void)
{
    TEST_ASSERT_TRUE(bsp_init());
    adc_raw = 2560;
    TEST_ASSERT_EQUAL_INT32(4125, bsp_motor_sample().current_ma);
    adc_raw = 1536;
    TEST_ASSERT_EQUAL_INT32(-4125, bsp_motor_sample().current_ma);
}

/**
 * @brief Positive duty drives forward with |duty| on the PWM and the bridge enabled.
 * @relation(SWR-BSP-003, scope=function, role=Test)
 */
void test_apply_forward(void)
{
    bsp_motor_apply((drive_cmd_t){ .enable = true, .duty = 600 });
    TEST_ASSERT_TRUE(out_level[BOARD_PIN_MOTOR_DIR]);
    TEST_ASSERT_EQUAL_UINT16(600, pwm_duty);
    TEST_ASSERT_TRUE(out_level[BOARD_PIN_MOTOR_ENABLE]);
}

/**
 * @brief Negative duty drives in reverse with its magnitude on the PWM.
 * @relation(SWR-BSP-003, scope=function, role=Test)
 */
void test_apply_reverse(void)
{
    bsp_motor_apply((drive_cmd_t){ .enable = true, .duty = -1000 });
    TEST_ASSERT_FALSE(out_level[BOARD_PIN_MOTOR_DIR]);
    TEST_ASSERT_EQUAL_UINT16(1000, pwm_duty);
    TEST_ASSERT_TRUE(out_level[BOARD_PIN_MOTOR_ENABLE]);
}

/**
 * @brief A disabled command releases the bridge enable.
 * @relation(SWR-BSP-003, scope=function, role=Test)
 */
void test_apply_disabled(void)
{
    bsp_motor_apply((drive_cmd_t){ .enable = false, .duty = 0 });
    TEST_ASSERT_EQUAL_UINT16(0, pwm_duty);
    TEST_ASSERT_FALSE(out_level[BOARD_PIN_MOTOR_ENABLE]);
}

/**
 * @brief A button reads as pressed when its pin is at the pressed level.
 * @relation(SWR-APP-002, scope=function, role=Test)
 */
void test_buttons_follow_pressed_level(void)
{
    bsp_buttons_t buttons = bsp_read_buttons();
    TEST_ASSERT_FALSE(buttons.start_pressed);
    TEST_ASSERT_FALSE(buttons.stop_pressed);

    in_level[BOARD_PIN_BUTTON_START] = BOARD_BUTTON_PRESSED_LEVEL;
    buttons = bsp_read_buttons();
    TEST_ASSERT_TRUE(buttons.start_pressed);
    TEST_ASSERT_FALSE(buttons.stop_pressed);

    in_level[BOARD_PIN_BUTTON_STOP] = BOARD_BUTTON_PRESSED_LEVEL;
    TEST_ASSERT_TRUE(bsp_read_buttons().stop_pressed);
}
