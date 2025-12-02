from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    # Kamera node
    camera_node = Node(
        package="my_markers",
        executable="png_reader",
        name="png_reader",
        output="screen"
    )

    # Szegmentációs CNN node
    seg_node = Node(
        package="road_seg",
        executable="seg_node",
        name="seg_node",
        output="screen"
    )

    # BEV node
    bev_node = Node(
        package="road_bev",
        executable="bev_node",
        name="bev_node",
        output="screen"
    )

    # Marker node (MarkerArray)
    marker_node = Node(
        package="my_markers",
        executable="marker_node",
        name="marker_node",
        output="screen"
    )

    # RViz2
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
    )

    return LaunchDescription([
        camera_node,
        seg_node,
        bev_node,
        marker_node,
        rviz_node
    ])
