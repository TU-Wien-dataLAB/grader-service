# LTI Plugin

The LTI (Learning Tools Interoperability) plugin is an optional feature that can be enabled via traitlets.
LTI is a standard developed by IMS Global that allows seamless integration between learning applications 
and Learning Management Systems (LMS), such as Moodle.

When enabled, this plugin allows submission scores to be synced back to a connected Moodle course,
streamlining the grading process.

:::{note}
Currently, the plugin is limited to syncing grades to **one** external 
LTI tool. This means that if you're using the LTI authenticator to support 
multiple LTI tools (each with a different client ID), only one of them can receive synced grades through 
the plugin. 
:::

To find out more, visit the [reference page](../reference/plugin_traits.md).