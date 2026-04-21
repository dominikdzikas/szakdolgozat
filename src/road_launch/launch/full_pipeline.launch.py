from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os



def generate_launch_description():
    road_launch_share = get_package_share_directory("road_launch")
    rviz_config = os.path.join(road_launch_share, "rviz", "full_pipeline.rviz")
    
    video_arg = DeclareLaunchArgument(
        "video_path",
        default_value="",
        description="Path to video file"
    )

    model_arg = DeclareLaunchArgument(
        "model_path",
        default_value="",
        description="Path to model checkpoint file"
    )
    bev_config_arg = DeclareLaunchArgument(
        "bev_config",
        default_value="",
        description="Path to BEV config yaml file"
    )

    # Kamera node
    camera_node = Node(
        package="my_markers",
        executable="video_publisher",
        name="video_publisher",
        output="screen",
        parameters=[{
            "video_path": LaunchConfiguration("video_path")
        }]
    )

    # Szegmentációs CNN node
    seg_node = Node(
        package="road_seg",
        executable="seg_node",
        name="seg_node",
        output="screen",
        parameters=[{
            "model_path": LaunchConfiguration("model_path")
        }]
    )

    # BEV node
    bev_node = Node(
        package="road_bev",
        executable="bev_node",
        name="bev_node",
        output="screen",
        parameters=[{
            "bev_config": LaunchConfiguration("bev_config")
        }]
    )

    #lidar_ground_truth_node = Node(
    #    package="road_bev",
    #    executable="lidar_ground_truth",
    #    name="lidar_ground_truth",
    #    output="screen"
    #)

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
        arguments=["-d", rviz_config],
        output="screen",
    )

    return LaunchDescription([
        video_arg,
        model_arg,
        bev_config_arg,
        camera_node,
        seg_node,
        bev_node,
        #lidar_ground_truth_node,
        marker_node,
        rviz_node
    ])
